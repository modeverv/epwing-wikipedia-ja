from __future__ import annotations

import io
import json
import tarfile
from datetime import UTC, datetime
from pathlib import Path

from wikiepwing.config import load_config
from wikiepwing.ingest.orchestrate import run_ingest
from wikiepwing.ingest.validate import ValidationLimits
from wikiepwing.model.database import connect_model_database
from wikiepwing.model.validate import ModelValidationLimits
from wikiepwing.normalize.orchestrate import run_normalize
from wikiepwing.normalize.pipeline import NormalizeOptions
from wikiepwing.render.generate import run_generate
from wikiepwing.render.verify import verify_entries_jsonl
from wikiepwing.source.register import LocalSourceFile, register_local_source

RAW_MIGRATIONS = Path(__file__).parents[1] / "migrations" / "raw"
MODEL_MIGRATIONS = Path(__file__).parents[1] / "migrations" / "model"
HUNDRED_ARTICLES_PATH = Path("tests/fixtures/enterprise/hundred_articles.ndjson")
DEFAULT_CONFIG = Path("config/default.toml")
FULL_PROFILE_CONFIG = Path("config/profiles/full.toml")


def _make_tar_gz(destination: Path, *, member_name: str, ndjson_path: Path) -> None:
    body = ndjson_path.read_bytes()
    with tarfile.open(destination, mode="w:gz") as archive:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(body)
        archive.addfile(info, io.BytesIO(body))


def test_full_profile_build_over_hundred_article_fixture(tmp_path: Path) -> None:
    # TASK-Q006's acceptance gate: the same shape as TASK-P002/P003's
    # Mini/Lite profile tests, for the Full profile. Wiring config values
    # beyond images.enabled into normalize/render behavior remains out of
    # scope here, per the same reasoning as those tasks.
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    chunk_tar = downloads / "chunk_0.tar.gz"
    _make_tar_gz(chunk_tar, member_name="chunk_0.ndjson", ndjson_path=HUNDRED_ARTICLES_PATH)

    acquired = register_local_source(
        [LocalSourceFile(source_path=chunk_tar, chunk_identifier="jawiki_namespace_0_chunk_0")],
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

    config = load_config(DEFAULT_CONFIG, [FULL_PROFILE_CONFIG])
    assert config.profile == "full"
    validation_limits = ValidationLimits.from_config(config, expected_namespace_id=0)
    raw_database_path = tmp_path / "work" / "raw.sqlite3"
    ingest_result = run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=raw_database_path,
        migrations_path=RAW_MIGRATIONS,
        manifest_path=tmp_path / "manifests" / "30-ingest.json",
        run_id="full-profile-ingest",
        validation_limits=validation_limits,
        git_commit="abc1234",
    )
    assert ingest_result.manifest.status == "complete"
    assert ingest_result.manifest.metrics.records_written == 100

    model_validation_limits = ModelValidationLimits.from_config(config)
    normalize_section = config.section("normalize")
    normalize_options = NormalizeOptions(
        max_dom_depth=normalize_section["max_dom_depth"],  # type: ignore[arg-type]
        html_recover=normalize_section["html_recover"],  # type: ignore[arg-type]
        remove_edit_ui=normalize_section["remove_edit_ui"],  # type: ignore[arg-type]
        remove_navboxes=normalize_section["remove_navboxes"],  # type: ignore[arg-type]
        remove_authority_control=normalize_section["remove_authority_control"],  # type: ignore[arg-type]
        images_enabled=config.section("images")["enabled"],  # type: ignore[arg-type]
    )
    model_database_path = tmp_path / "work" / "model.sqlite3"
    normalize_result = run_normalize(
        raw_database_path=raw_database_path,
        model_database_path=model_database_path,
        model_migrations_path=MODEL_MIGRATIONS,
        manifest_path=tmp_path / "manifests" / "40-normalize.json",
        run_id="full-profile-normalize",
        model_validation_limits=model_validation_limits,
        normalize_options=normalize_options,
        git_commit="abc1234",
    )
    assert normalize_result.manifest.status == "complete"
    assert normalize_result.manifest.metrics.articles_read == 100

    with connect_model_database(model_database_path) as connection:
        media_count = connection.execute("SELECT COUNT(*) FROM media_references").fetchone()[0]
        assert media_count > 0, "Full profile (images.enabled=true) should still produce images"

    entries_path = tmp_path / "entries.jsonl"
    generate_result = run_generate(
        model_database_path=model_database_path,
        entries_path=entries_path,
        manifest_path=tmp_path / "manifests" / "50-generate.json",
        run_id="full-profile-generate",
        git_commit="abc1234",
    )
    assert generate_result.manifest.status == "complete"
    assert generate_result.manifest.metrics.entries_written == 100

    lines = entries_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 100
    tags = {json.loads(line)["tag"] for line in lines}
    assert len(tags) == 100

    verification = verify_entries_jsonl(entries_path)
    assert verification.ok is True, verification.issues
    assert verification.entry_count == 100
