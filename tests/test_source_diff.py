from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.source.lockfile import SourceLockAcquirer, SourceLockFile, build_source_lock
from wikiepwing.source_diff import build_update_report, compute_source_diff, write_update_report


def _lock(*, snapshot_version: str, files: tuple[SourceLockFile, ...]) -> object:
    return build_source_lock(
        provider="wikimedia-enterprise-snapshot",
        project="jawiki",
        namespace=0,
        snapshot_identifier="jawiki_namespace_0",
        snapshot_version=snapshot_version,
        date_modified=datetime(2026, 7, 1, tzinfo=UTC),
        downloaded_at=datetime(2026, 7, 16, tzinfo=UTC),
        files=files,
        metadata_response_sha256="0" * 64,
        acquirer=SourceLockAcquirer(name="wikiepwing", version="0.1.0", git_commit="abc1234"),
    )


def _file(identifier: str, *, size: int = 100, sha256: str | None = None) -> SourceLockFile:
    return SourceLockFile(
        relative_path=f"{identifier}.tar.gz",
        chunk_identifier=identifier,
        size_bytes=size,
        sha256=sha256 or ("0" * 63 + "1"),
        media_type="application/gzip",
    )


def test_first_acquire_reports_all_chunks_added() -> None:
    new = _lock(snapshot_version="v2", files=(_file("chunk_0"), _file("chunk_1")))

    diff = compute_source_diff(None, new)  # type: ignore[arg-type]

    assert diff.previous_snapshot_version is None
    assert diff.version_changed is True
    assert diff.added_chunk_identifiers == ("chunk_0", "chunk_1")
    assert diff.removed_chunk_identifiers == ()
    assert diff.changed_chunk_identifiers == ()
    assert diff.unchanged_chunk_count == 0
    assert diff.previous_total_size_bytes is None
    assert diff.new_total_size_bytes == 200
    assert diff.size_delta_bytes == 200


def test_same_version_no_changes() -> None:
    files = (_file("chunk_0"), _file("chunk_1"))
    previous = _lock(snapshot_version="v1", files=files)
    new = _lock(snapshot_version="v1", files=files)

    diff = compute_source_diff(previous, new)  # type: ignore[arg-type]

    assert diff.version_changed is False
    assert diff.added_chunk_identifiers == ()
    assert diff.removed_chunk_identifiers == ()
    assert diff.changed_chunk_identifiers == ()
    assert diff.unchanged_chunk_count == 2
    assert diff.size_delta_bytes == 0


def test_detects_added_removed_and_changed_chunks() -> None:
    previous = _lock(
        snapshot_version="v1",
        files=(_file("chunk_0", size=100), _file("chunk_1", size=100), _file("chunk_2", size=100)),
    )
    new = _lock(
        snapshot_version="v2",
        files=(
            _file("chunk_0", size=100),
            _file("chunk_1", size=150, sha256="1" * 64),
            _file("chunk_3", size=100),
        ),
    )

    diff = compute_source_diff(previous, new)  # type: ignore[arg-type]

    assert diff.version_changed is True
    assert diff.added_chunk_identifiers == ("chunk_3",)
    assert diff.removed_chunk_identifiers == ("chunk_2",)
    assert diff.changed_chunk_identifiers == ("chunk_1",)
    assert diff.unchanged_chunk_count == 1
    assert diff.previous_total_size_bytes == 300
    assert diff.new_total_size_bytes == 350
    assert diff.size_delta_bytes == 50


def test_build_update_report_requires_timezone_aware_datetime() -> None:
    previous = None
    new = _lock(snapshot_version="v1", files=(_file("chunk_0"),))
    diff = compute_source_diff(previous, new)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        build_update_report(diff, updated_at=datetime(2026, 7, 16))


def test_build_update_report_payload_shape() -> None:
    new = _lock(snapshot_version="v1", files=(_file("chunk_0"),))
    diff = compute_source_diff(None, new)  # type: ignore[arg-type]

    report = build_update_report(diff, updated_at=datetime(2026, 7, 16, tzinfo=UTC))

    assert report["schema_version"] == 1
    assert report["updated_at"] == "2026-07-16T00:00:00Z"
    assert report["diff"]["new_snapshot_version"] == "v1"


def test_write_update_report_writes_deterministic_json(tmp_path: Path) -> None:
    new = _lock(snapshot_version="v1", files=(_file("chunk_0"),))
    diff = compute_source_diff(None, new)  # type: ignore[arg-type]
    report = build_update_report(diff, updated_at=datetime(2026, 7, 16, tzinfo=UTC))
    output_path = tmp_path / "update-report.json"

    write_update_report(report, output_path)

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded == report
