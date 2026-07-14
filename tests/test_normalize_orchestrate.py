from __future__ import annotations

import io
import tarfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.config import load_config
from wikiepwing.ingest.orchestrate import run_ingest
from wikiepwing.ingest.validate import ValidationLimits
from wikiepwing.model.database import connect_model_database
from wikiepwing.model.validate import ModelValidationLimits
from wikiepwing.normalize.orchestrate import NormalizeError, read_manifest_status, run_normalize
from wikiepwing.normalize.pipeline import NormalizeOptions
from wikiepwing.source.register import LocalSourceFile, register_local_source

RAW_MIGRATIONS = Path(__file__).parents[1] / "migrations" / "raw"
MODEL_MIGRATIONS = Path(__file__).parents[1] / "migrations" / "model"
NORMAL_PATH = Path("tests/fixtures/enterprise/normal_articles.ndjson")
DEFAULT_CONFIG = Path("config/default.toml")


def _make_tar_gz(destination: Path, *, member_name: str, ndjson_path: Path) -> None:
    body = ndjson_path.read_bytes()
    with tarfile.open(destination, mode="w:gz") as archive:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(body)
        archive.addfile(info, io.BytesIO(body))


def _build_raw_database(tmp_path: Path) -> Path:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    normal_tar = downloads / "chunk_0.tar.gz"
    _make_tar_gz(normal_tar, member_name="chunk_0.ndjson", ndjson_path=NORMAL_PATH)

    acquired = register_local_source(
        [LocalSourceFile(source_path=normal_tar, chunk_identifier="jawiki_namespace_0_chunk_0")],
        project="jawiki",
        namespace=0,
        snapshot_identifier="jawiki_namespace_0",
        snapshot_version="test-2026-07-14",
        date_modified=datetime(2026, 7, 14, tzinfo=UTC),
        sources_root=tmp_path / "sources",
        acquirer_name="wikiepwing",
        acquirer_version="0.1.0",
        acquirer_git_commit="abc1234",
    )
    config = load_config(DEFAULT_CONFIG)
    limits = ValidationLimits.from_config(config, expected_namespace_id=0)
    raw_database_path = tmp_path / "work" / "raw.sqlite3"
    run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=raw_database_path,
        migrations_path=RAW_MIGRATIONS,
        manifest_path=tmp_path / "manifests" / "30-ingest.json",
        run_id="test-ingest-run",
        validation_limits=limits,
        git_commit="abc1234",
    )
    return raw_database_path


def _model_validation_limits() -> ModelValidationLimits:
    config = load_config(DEFAULT_CONFIG)
    return ModelValidationLimits.from_config(config)


def _normalize_options() -> NormalizeOptions:
    config = load_config(DEFAULT_CONFIG)
    normalize_section = config.section("normalize")
    return NormalizeOptions(
        max_dom_depth=normalize_section["max_dom_depth"],  # type: ignore[arg-type]
        html_recover=normalize_section["html_recover"],  # type: ignore[arg-type]
        remove_edit_ui=normalize_section["remove_edit_ui"],  # type: ignore[arg-type]
        remove_navboxes=normalize_section["remove_navboxes"],  # type: ignore[arg-type]
        remove_authority_control=normalize_section["remove_authority_control"],  # type: ignore[arg-type]
    )


def test_normalize_end_to_end_over_normal_fixture(tmp_path: Path) -> None:
    raw_database_path = _build_raw_database(tmp_path)

    result = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=tmp_path / "work" / "model.sqlite3",
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=tmp_path / "manifests" / "40-normalize.json",
        run_id="test-normalize-run",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
        git_commit="abc1234",
    )

    assert result.manifest.status == "complete"
    assert result.manifest.metrics.articles_read == 10
    assert result.manifest.metrics.articles_read == (
        result.manifest.metrics.articles_written + result.manifest.metrics.articles_rejected
    )

    with connect_model_database(result.model_database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        assert count == 10
        row = connection.execute(
            "SELECT normalize_status, block_count, article_logical_hash "
            "FROM articles ORDER BY page_id LIMIT 1"
        ).fetchone()
        assert row["normalize_status"] in ("complete", "fallback", "rejected")
        assert row["block_count"] >= 0
        assert len(row["article_logical_hash"]) == 64
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_normalize_is_idempotent_on_rerun(tmp_path: Path) -> None:
    raw_database_path = _build_raw_database(tmp_path)
    model_database_path = tmp_path / "work" / "model.sqlite3"
    manifest_path = tmp_path / "manifests" / "40-normalize.json"

    run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-one",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
    )
    result = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-two",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
    )

    assert result.manifest.status == "complete"
    with connect_model_database(model_database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        assert count == 10


def test_normalize_refuses_running_manifest_without_force(tmp_path: Path) -> None:
    raw_database_path = _build_raw_database(tmp_path)
    manifest_path = tmp_path / "manifests" / "40-normalize.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text('{"status": "running"}', encoding="utf-8")

    with pytest.raises(NormalizeError, match="still 'running'"):
        run_normalize(
            raw_database_path=raw_database_path,
            model_database_path=tmp_path / "work" / "model.sqlite3",
            model_migrations_path=MODEL_MIGRATIONS,
            manifest_path=manifest_path,
            run_id="test-run",
            model_validation_limits=_model_validation_limits(),
            normalize_options=_normalize_options(),
        )


def test_normalize_force_proceeds_over_running_manifest(tmp_path: Path) -> None:
    raw_database_path = _build_raw_database(tmp_path)
    manifest_path = tmp_path / "manifests" / "40-normalize.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text('{"status": "running"}', encoding="utf-8")

    result = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=tmp_path / "work" / "model.sqlite3",
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="test-run",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
        force=True,
    )

    assert result.manifest.status == "complete"


def test_normalize_skips_rerun_when_previous_run_is_complete_and_unchanged(
    tmp_path: Path,
) -> None:
    raw_database_path = _build_raw_database(tmp_path)
    model_database_path = tmp_path / "work" / "model.sqlite3"
    manifest_path = tmp_path / "manifests" / "40-normalize.json"

    first = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-one",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
    )

    second = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-two",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
    )

    assert second.manifest.run_id == first.manifest.run_id
    assert second.manifest.status == "complete"


def test_normalize_force_reruns_despite_complete_manifest(tmp_path: Path) -> None:
    raw_database_path = _build_raw_database(tmp_path)
    model_database_path = tmp_path / "work" / "model.sqlite3"
    manifest_path = tmp_path / "manifests" / "40-normalize.json"

    run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-one",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
    )

    second = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-two",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
        force=True,
    )

    assert second.manifest.run_id == "run-two"


def test_read_manifest_status_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_manifest_status(tmp_path / "missing.json") is None
