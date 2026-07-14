from __future__ import annotations

import io
import multiprocessing
import os
import signal
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.config import load_config
from wikiepwing.ingest.orchestrate import run_ingest
from wikiepwing.ingest.validate import ValidationLimits
from wikiepwing.ingest.zstd_codec import decompress
from wikiepwing.model.canonical import decode_article
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


def test_categories_survive_raw_ingest_through_normalize(tmp_path: Path) -> None:
    """TASK-L004: the category appendix (TASK-H007) is only useful if categories
    actually survive ingest -> normalize into Article.categories; no test
    checked that end-to-end before this one."""
    raw_database_path = _build_raw_database(tmp_path)

    result = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=tmp_path / "work" / "model.sqlite3",
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=tmp_path / "manifests" / "40-normalize.json",
        run_id="test-normalize-run",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
    )

    with connect_model_database(result.model_database_path) as connection:
        row = connection.execute(
            "SELECT article_json_zstd FROM articles WHERE page_id = 900001"
        ).fetchone()
        article = decode_article(decompress(row["article_json_zstd"]))
        assert article.categories == ("Category:Emacs",)


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


def test_normalize_reruns_when_output_file_is_corrupted_since_last_run(tmp_path: Path) -> None:
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
    assert first.manifest.status == "complete"

    # Simulate the output file being corrupted/truncated after the manifest
    # recorded it as complete; a naive resume that only compares
    # status/stage_version/inputs would wrongly trust this stale manifest.
    model_database_path.write_bytes(b"not a sqlite file")

    second = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-two",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
    )

    assert second.manifest.run_id == "run-two"
    assert second.manifest.status == "complete"
    with connect_model_database(model_database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        assert count == 10


def test_normalize_killed_mid_run_leaves_manifest_running_and_force_restart_succeeds(
    tmp_path: Path,
) -> None:
    """PLAN.md Phase 9: "normalize途中kill" / "interrupted stageだけ再実行".

    Runs `run_normalize` in a forked child process with an artificial delay
    between articles, sends it SIGKILL partway through, then confirms: the
    manifest is left showing "running" (so a plain rerun is refused), and a
    forced rerun completes successfully with the correct final article count.
    """
    raw_database_path = _build_raw_database(tmp_path)
    model_database_path = tmp_path / "work" / "model.sqlite3"
    manifest_path = tmp_path / "manifests" / "40-normalize.json"

    ctx = multiprocessing.get_context("fork")
    process = ctx.Process(
        target=_run_normalize_slowly,
        args=(raw_database_path, model_database_path, manifest_path),
    )
    process.start()
    time.sleep(0.4)
    os.kill(process.pid, signal.SIGKILL)
    process.join(timeout=5)

    assert process.exitcode != 0
    assert read_manifest_status(manifest_path) == "running"

    with pytest.raises(NormalizeError, match="still 'running'"):
        run_normalize(
            raw_database_path=raw_database_path,
            model_database_path=model_database_path,
            model_migrations_path=MODEL_MIGRATIONS,
            manifest_path=manifest_path,
            run_id="restart-run",
            model_validation_limits=_model_validation_limits(),
            normalize_options=_normalize_options(),
        )

    result = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="restart-run",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
        force=True,
    )

    assert result.manifest.status == "complete"
    with connect_model_database(model_database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        assert count == 10
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def _run_normalize_slowly(
    raw_database_path: Path, model_database_path: Path, manifest_path: Path
) -> None:
    run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=manifest_path,
        run_id="killed-run",
        model_validation_limits=_model_validation_limits(),
        normalize_options=_normalize_options(),
        batch_size=1,
        on_progress=lambda _metrics: time.sleep(0.2),
    )


def test_read_manifest_status_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_manifest_status(tmp_path / "missing.json") is None
