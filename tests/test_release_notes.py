from __future__ import annotations

from datetime import UTC, datetime

from wikiepwing.release_notes import render_release_notes
from wikiepwing.source.lockfile import SourceLockAcquirer, SourceLockFile, build_source_lock
from wikiepwing.source_diff import build_update_report, compute_source_diff


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


def test_initial_acquisition_notes() -> None:
    new = _lock(snapshot_version="v1", files=(_file("chunk_0"),))
    diff = compute_source_diff(None, new)  # type: ignore[arg-type]
    report = build_update_report(diff, updated_at=datetime(2026, 7, 16, tzinfo=UTC))

    notes = render_release_notes(report, project="jawiki")

    assert "Initial acquisition of Snapshot version `v1`" in notes
    assert "Chunks added: 1" in notes
    assert "Total size: 100 B." in notes


def test_version_changed_notes_include_chunk_and_size_deltas() -> None:
    previous = _lock(
        snapshot_version="v1",
        files=(_file("chunk_0", size=1000), _file("chunk_1", size=1000)),
    )
    new = _lock(
        snapshot_version="v2",
        files=(
            _file("chunk_0", size=1000),
            _file("chunk_1", size=2000, sha256="1" * 64),
            _file("chunk_2", size=1000),
        ),
    )
    diff = compute_source_diff(previous, new)  # type: ignore[arg-type]
    report = build_update_report(diff, updated_at=datetime(2026, 7, 16, tzinfo=UTC))

    notes = render_release_notes(report, project="jawiki")

    assert "Snapshot version changed: `v1` -> `v2`" in notes
    assert "Chunks added: 1" in notes
    assert "Chunks removed: 0" in notes
    assert "Chunks changed: 1" in notes
    assert "Chunks unchanged: 1" in notes
    assert "+" in notes


def test_unchanged_version_notes_say_so() -> None:
    files = (_file("chunk_0"),)
    previous = _lock(snapshot_version="v1", files=files)
    new = _lock(snapshot_version="v1", files=files)
    diff = compute_source_diff(previous, new)  # type: ignore[arg-type]
    report = build_update_report(diff, updated_at=datetime(2026, 7, 16, tzinfo=UTC))

    notes = render_release_notes(report, project="jawiki")

    assert "Snapshot version unchanged: `v1`" in notes
    assert "0 B" in notes


def test_human_size_uses_larger_units() -> None:
    new = _lock(snapshot_version="v1", files=(_file("chunk_0", size=5 * 1024 * 1024),))
    diff = compute_source_diff(None, new)  # type: ignore[arg-type]
    report = build_update_report(diff, updated_at=datetime(2026, 7, 16, tzinfo=UTC))

    notes = render_release_notes(report, project="jawiki")

    assert "5.0 MB" in notes
