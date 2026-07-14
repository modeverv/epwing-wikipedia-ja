from __future__ import annotations

import io
import tarfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.config import load_config
from wikiepwing.ingest.database import connect_raw_database
from wikiepwing.ingest.orchestrate import run_ingest
from wikiepwing.ingest.validate import ValidationLimits
from wikiepwing.ingest.verify import verify_raw_database
from wikiepwing.source.register import LocalSourceFile, register_local_source

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "raw"
NORMAL_PATH = Path("tests/fixtures/enterprise/normal_articles.ndjson")
DEFAULT_CONFIG = Path("config/default.toml")


def _ingested_connection(tmp_path: Path):
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    tar_path = downloads / "chunk_0.tar.gz"
    body = NORMAL_PATH.read_bytes()
    with tarfile.open(tar_path, mode="w:gz") as archive:
        info = tarfile.TarInfo(name="chunk_0.ndjson")
        info.size = len(body)
        archive.addfile(info, io.BytesIO(body))

    acquired = register_local_source(
        [LocalSourceFile(source_path=tar_path, chunk_identifier="jawiki_namespace_0_chunk_0")],
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
    result = run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=tmp_path / "work" / "raw.sqlite3",
        migrations_path=MIGRATIONS,
        manifest_path=tmp_path / "manifests" / "30-ingest.json",
        run_id="test-run",
        validation_limits=limits,
    )
    return connect_raw_database(result.raw_database_path)


def test_verifies_clean_ingested_database(tmp_path: Path) -> None:
    connection = _ingested_connection(tmp_path)

    result = verify_raw_database(connection)

    assert result.ok is True
    assert result.integrity_check == "ok"
    assert result.foreign_key_errors == 0
    assert result.counts.accepted_articles == 10
    assert result.counts.rejected_articles == 0
    assert result.counts.redirects >= 1
    assert result.counts.licenses >= 1
    assert result.sample_checked > 0
    assert result.sample_failures == ()


def test_sample_size_zero_skips_decompression_but_still_checks_integrity(tmp_path: Path) -> None:
    connection = _ingested_connection(tmp_path)

    result = verify_raw_database(connection, sample_size=0)

    assert result.sample_checked == 0
    assert result.sample_failures == ()
    assert result.ok is True


def test_detects_corrupted_html_blob(tmp_path: Path) -> None:
    connection = _ingested_connection(tmp_path)
    page_id = connection.execute(
        "SELECT page_id FROM articles WHERE html_zstd IS NOT NULL ORDER BY page_id LIMIT 1"
    ).fetchone()[0]
    connection.execute(
        "UPDATE articles SET html_zstd = ? WHERE page_id = ?", (b"not a zstd frame", page_id)
    )
    connection.commit()

    result = verify_raw_database(connection, sample_size=100)

    assert result.ok is False
    assert any(f"page_id={page_id}" in failure for failure in result.sample_failures)


def test_negative_sample_size_is_rejected(tmp_path: Path) -> None:
    connection = _ingested_connection(tmp_path)

    with pytest.raises(ValueError, match="sample_size"):
        verify_raw_database(connection, sample_size=-1)


def test_payload_matches_dataclass_fields(tmp_path: Path) -> None:
    connection = _ingested_connection(tmp_path)

    result = verify_raw_database(connection)
    payload = result.payload()

    assert payload["ok"] is True
    assert payload["counts"]["accepted_articles"] == 10
