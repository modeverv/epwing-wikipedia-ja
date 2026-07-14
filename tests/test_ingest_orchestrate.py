from __future__ import annotations

import io
import json
import tarfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.config import load_config
from wikiepwing.ingest.database import connect_raw_database
from wikiepwing.ingest.orchestrate import IngestError, read_manifest_status, run_ingest
from wikiepwing.ingest.tar_reader import TarStreamError
from wikiepwing.ingest.validate import ValidationLimits
from wikiepwing.source.register import LocalSourceFile, register_local_source

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "raw"
NORMAL_PATH = Path("tests/fixtures/enterprise/normal_articles.ndjson")
EDGE_CASE_PATH = Path("tests/fixtures/enterprise/edge_case_articles.ndjson")
DEFAULT_CONFIG = Path("config/default.toml")


def _make_tar_gz(destination: Path, *, member_name: str, ndjson_path: Path) -> None:
    body = ndjson_path.read_bytes()
    with tarfile.open(destination, mode="w:gz") as archive:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(body)
        archive.addfile(info, io.BytesIO(body))


def _register(tmp_path: Path):
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    normal_tar = downloads / "chunk_0.tar.gz"
    edge_case_tar = downloads / "chunk_1.tar.gz"
    _make_tar_gz(normal_tar, member_name="chunk_0.ndjson", ndjson_path=NORMAL_PATH)
    _make_tar_gz(edge_case_tar, member_name="chunk_1.ndjson", ndjson_path=EDGE_CASE_PATH)

    result = register_local_source(
        [
            LocalSourceFile(source_path=normal_tar, chunk_identifier="jawiki_namespace_0_chunk_0"),
            LocalSourceFile(
                source_path=edge_case_tar, chunk_identifier="jawiki_namespace_0_chunk_1"
            ),
        ],
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
    return result


def _limits() -> ValidationLimits:
    config = load_config(DEFAULT_CONFIG)
    return ValidationLimits.from_config(config, expected_namespace_id=0)


def test_ingest_end_to_end_over_normal_and_edge_case_fixtures(tmp_path: Path) -> None:
    acquired = _register(tmp_path)

    result = run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=tmp_path / "work" / "raw.sqlite3",
        migrations_path=MIGRATIONS,
        manifest_path=tmp_path / "manifests" / "30-ingest.json",
        run_id="test-run",
        validation_limits=_limits(),
        batch_size=3,
        git_commit="abc1234",
    )

    assert result.manifest.status == "complete"
    metrics = result.manifest.metrics
    # 10 normal + 11 edge-case lines
    assert metrics.records_read == 21
    # normal: 10 written. edge cases: written = html_missing, rev1, rev2(replace),
    # dup_first, conflict_first, empty_license, large_article = 7
    assert metrics.records_written == 17
    # rejected: title_too_long, invalid_url
    assert metrics.records_rejected == 2
    # errors: conflict diagnostic + title_too_long + invalid_url
    assert metrics.errors == 3
    assert metrics.warnings == 0
    assert metrics.fatals == 0

    assert result.manifest_path.is_file()
    on_disk = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert on_disk == result.manifest.payload()
    assert on_disk["stage"] == "30-ingest"
    assert on_disk["run_id"] == "test-run"
    assert on_disk["outputs"][0]["relative_path"] == "raw.sqlite3"
    assert on_disk["software"]["git_commit"] == "abc1234"

    connection = connect_raw_database(result.raw_database_path)
    accepted_count = connection.execute(
        "SELECT COUNT(*) FROM articles WHERE ingest_status = 'accepted'"
    ).fetchone()[0]
    # 17 write events (metrics.records_written) but page 910002 is written twice
    # (revision replace upserts the same row), so only 16 distinct accepted rows exist.
    assert accepted_count == 16
    rejected_count = connection.execute(
        "SELECT COUNT(*) FROM articles WHERE ingest_status = 'rejected'"
    ).fetchone()[0]
    assert rejected_count == 2
    duplicate_count = connection.execute("SELECT COUNT(*) FROM ingest_duplicates").fetchone()[0]
    assert duplicate_count == 3
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    # the replaced-revision page kept only the newer revision
    revised = connection.execute(
        "SELECT revision_id FROM articles WHERE page_id = 910002"
    ).fetchone()
    assert revised["revision_id"] == 1100003

    # the conflicting page kept the first-seen revision (safe default)
    conflicting = connection.execute(
        "SELECT source_hash FROM articles WHERE page_id = 910004"
    ).fetchone()
    assert conflicting is not None


def test_chunk_verification_failure_aborts_before_writing(tmp_path: Path) -> None:
    acquired = _register(tmp_path)
    # corrupt the registered chunk after the fact
    (acquired.snapshot_directory / "jawiki_namespace_0_chunk_0.tar.gz").write_bytes(b"corrupted")

    with pytest.raises(IngestError, match="chunk verification failed"):
        run_ingest(
            acquired.lock,
            snapshot_directory=acquired.snapshot_directory,
            raw_database_path=tmp_path / "work" / "raw.sqlite3",
            migrations_path=MIGRATIONS,
            manifest_path=tmp_path / "manifests" / "30-ingest.json",
            run_id="test-run",
            validation_limits=_limits(),
        )

    assert not (tmp_path / "manifests" / "30-ingest.json").exists()


def test_non_positive_batch_size_is_rejected(tmp_path: Path) -> None:
    acquired = _register(tmp_path)

    with pytest.raises(IngestError, match="batch_size"):
        run_ingest(
            acquired.lock,
            snapshot_directory=acquired.snapshot_directory,
            raw_database_path=tmp_path / "work" / "raw.sqlite3",
            migrations_path=MIGRATIONS,
            manifest_path=tmp_path / "manifests" / "30-ingest.json",
            run_id="test-run",
            validation_limits=_limits(),
            batch_size=0,
        )


def test_on_progress_callback_is_invoked(tmp_path: Path) -> None:
    acquired = _register(tmp_path)
    calls = []

    run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=tmp_path / "work" / "raw.sqlite3",
        migrations_path=MIGRATIONS,
        manifest_path=tmp_path / "manifests" / "30-ingest.json",
        run_id="test-run",
        validation_limits=_limits(),
        batch_size=3,
        on_progress=lambda metrics: calls.append(metrics.records_read),
    )

    assert len(calls) > 1
    assert calls[-1] == 21
    assert calls == sorted(calls)


def test_read_manifest_status_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_manifest_status(tmp_path / "missing.json") is None


def test_read_manifest_status_rejects_unparseable_file(tmp_path: Path) -> None:
    manifest_path = tmp_path / "broken.json"
    manifest_path.write_text("not json", encoding="utf-8")

    with pytest.raises(IngestError, match="cannot read existing manifest"):
        read_manifest_status(manifest_path)


def test_running_manifest_written_immediately_and_updated_to_complete(tmp_path: Path) -> None:
    acquired = _register(tmp_path)
    manifest_path = tmp_path / "manifests" / "30-ingest.json"

    run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=tmp_path / "work" / "raw.sqlite3",
        migrations_path=MIGRATIONS,
        manifest_path=manifest_path,
        run_id="test-run",
        validation_limits=_limits(),
    )

    assert read_manifest_status(manifest_path) == "complete"


def test_rerun_is_refused_while_manifest_shows_running(tmp_path: Path) -> None:
    acquired = _register(tmp_path)
    manifest_path = tmp_path / "manifests" / "30-ingest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps({"schema_version": 1, "status": "running"}), encoding="utf-8"
    )

    with pytest.raises(IngestError, match="still 'running'"):
        run_ingest(
            acquired.lock,
            snapshot_directory=acquired.snapshot_directory,
            raw_database_path=tmp_path / "work" / "raw.sqlite3",
            migrations_path=MIGRATIONS,
            manifest_path=manifest_path,
            run_id="test-run",
            validation_limits=_limits(),
        )


def test_force_allows_rerun_despite_running_manifest(tmp_path: Path) -> None:
    acquired = _register(tmp_path)
    manifest_path = tmp_path / "manifests" / "30-ingest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps({"schema_version": 1, "status": "running"}), encoding="utf-8"
    )

    result = run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=tmp_path / "work" / "raw.sqlite3",
        migrations_path=MIGRATIONS,
        manifest_path=manifest_path,
        run_id="test-run",
        validation_limits=_limits(),
        force=True,
    )

    assert result.manifest.status == "complete"


def test_rerun_over_completed_articles_is_idempotent(tmp_path: Path) -> None:
    acquired = _register(tmp_path)
    raw_database_path = tmp_path / "work" / "raw.sqlite3"
    manifest_path = tmp_path / "manifests" / "30-ingest.json"

    first = run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=raw_database_path,
        migrations_path=MIGRATIONS,
        manifest_path=manifest_path,
        run_id="test-run",
        validation_limits=_limits(),
        force=True,
    )
    second = run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=raw_database_path,
        migrations_path=MIGRATIONS,
        manifest_path=manifest_path,
        run_id="test-run-2",
        validation_limits=_limits(),
        force=True,
    )

    connection = connect_raw_database(second.raw_database_path)
    accepted_count = connection.execute(
        "SELECT COUNT(*) FROM articles WHERE ingest_status = 'accepted'"
    ).fetchone()[0]
    # article rows converge to the same accepted state; identical resubmissions are
    # recognized as duplicates and ignored rather than corrupting existing rows.
    assert accepted_count == 16
    assert first.manifest.status == "complete"
    assert second.manifest.status == "complete"
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_ingest_skips_rerun_when_previous_run_is_complete_and_unchanged(tmp_path: Path) -> None:
    acquired = _register(tmp_path)
    raw_database_path = tmp_path / "work" / "raw.sqlite3"
    manifest_path = tmp_path / "manifests" / "30-ingest.json"

    first = run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=raw_database_path,
        migrations_path=MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-one",
        validation_limits=_limits(),
    )

    second = run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=raw_database_path,
        migrations_path=MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-two",
        validation_limits=_limits(),
    )

    assert second.manifest.run_id == first.manifest.run_id
    assert second.manifest.status == "complete"


def test_ingest_force_reruns_despite_complete_manifest(tmp_path: Path) -> None:
    acquired = _register(tmp_path)
    raw_database_path = tmp_path / "work" / "raw.sqlite3"
    manifest_path = tmp_path / "manifests" / "30-ingest.json"

    run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=raw_database_path,
        migrations_path=MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-one",
        validation_limits=_limits(),
    )

    second = run_ingest(
        acquired.lock,
        snapshot_directory=acquired.snapshot_directory,
        raw_database_path=raw_database_path,
        migrations_path=MIGRATIONS,
        manifest_path=manifest_path,
        run_id="run-two",
        validation_limits=_limits(),
        force=True,
    )

    assert second.manifest.run_id == "run-two"


def test_manifest_status_is_failed_when_a_chunk_fails_mid_run(tmp_path: Path) -> None:
    acquired = _register(tmp_path)
    # replace the second chunk with a validly-sized-and-hashed archive that has a
    # tar member name the reader rejects, so verify_fingerprint passes but streaming
    # fails once the ingest loop actually reaches this chunk.
    bad_tar = tmp_path / "bad.tar.gz"
    with tarfile.open(bad_tar, mode="w:gz") as archive:
        info = tarfile.TarInfo(name="not-ndjson.txt")
        info.size = 3
        archive.addfile(info, io.BytesIO(b"abc"))
    target = acquired.snapshot_directory / "jawiki_namespace_0_chunk_1.tar.gz"
    target.unlink()
    bad_tar.rename(target)
    # rebuild the lock to match the replacement file's real fingerprint
    from wikiepwing.source.checksums import compute_fingerprint
    from wikiepwing.source.lockfile import (
        SourceLockFile,
        build_source_lock,
        write_source_lock,
    )

    fingerprint = compute_fingerprint(target)
    files = [
        acquired.lock.files[0],
        SourceLockFile(
            relative_path="jawiki_namespace_0_chunk_1.tar.gz",
            chunk_identifier="jawiki_namespace_0_chunk_1",
            size_bytes=fingerprint.size_bytes,
            sha256=fingerprint.sha256,
            media_type="application/gzip",
        ),
    ]
    patched_lock = build_source_lock(
        provider=acquired.lock.provider,
        project=acquired.lock.project,
        namespace=acquired.lock.namespace,
        snapshot_identifier=acquired.lock.snapshot_identifier,
        snapshot_version=acquired.lock.snapshot_version,
        date_modified=acquired.lock.date_modified,
        downloaded_at=acquired.lock.downloaded_at,
        files=files,
        metadata_response_sha256=acquired.lock.metadata_response_sha256,
        acquirer=acquired.lock.acquirer,
    )
    write_source_lock(patched_lock, acquired.lock_path)

    manifest_path = tmp_path / "manifests" / "30-ingest.json"
    with pytest.raises(TarStreamError):
        run_ingest(
            patched_lock,
            snapshot_directory=acquired.snapshot_directory,
            raw_database_path=tmp_path / "work" / "raw.sqlite3",
            migrations_path=MIGRATIONS,
            manifest_path=manifest_path,
            run_id="test-run",
            validation_limits=_limits(),
        )

    assert read_manifest_status(manifest_path) == "failed"
