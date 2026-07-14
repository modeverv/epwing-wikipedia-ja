from __future__ import annotations

import hashlib
import io
import json
import tarfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.source.inspect import InspectError, inspect_source
from wikiepwing.source.lockfile import (
    SourceLockAcquirer,
    SourceLockFile,
    build_source_lock,
    write_source_lock,
)


def _make_tar_gz(path: Path, *, member_name: str, ndjson_lines: list[bytes]) -> bytes:
    body = b"\n".join(ndjson_lines) + (b"\n" if ndjson_lines else b"")
    with tarfile.open(path, mode="w:gz") as archive:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(body)
        archive.addfile(info, io.BytesIO(body))
    return path.read_bytes()


def _lock_for(
    tmp_path: Path,
    snapshot_directory: Path,
    files: list[SourceLockFile],
) -> Path:
    lock = build_source_lock(
        provider="wikimedia-enterprise-snapshot",
        project="jawiki",
        namespace=0,
        snapshot_identifier="jawiki_namespace_0",
        snapshot_version="35061ecbd3bc55c31cffd4b46838673d",
        date_modified=datetime(2026, 7, 1, tzinfo=UTC),
        downloaded_at=datetime(2026, 7, 14, tzinfo=UTC),
        files=files,
        metadata_response_sha256="b" * 64,
        acquirer=SourceLockAcquirer(name="wikiepwing", version="0.1.0", git_commit="abc1234"),
    )
    lock_path = snapshot_directory / "source.lock.json"
    write_source_lock(lock, lock_path)
    return lock_path


def test_inspects_matching_file_with_tar_and_ndjson_sample(tmp_path: Path) -> None:
    snapshot_directory = tmp_path / "snapshot"
    snapshot_directory.mkdir()
    tar_path = snapshot_directory / "jawiki_namespace_0_chunk_0.tar.gz"
    records = [
        json.dumps({"name": "Emacs", "identifier": "1"}).encode(),
        json.dumps({"name": "Linux", "identifier": "2"}).encode(),
    ]
    raw = _make_tar_gz(tar_path, member_name="chunk_0.ndjson", ndjson_lines=records)
    fingerprint_sha256 = hashlib.sha256(raw).hexdigest()

    lock_path = _lock_for(
        tmp_path,
        snapshot_directory,
        [
            SourceLockFile(
                relative_path="jawiki_namespace_0_chunk_0.tar.gz",
                chunk_identifier="jawiki_namespace_0_chunk_0",
                size_bytes=len(raw),
                sha256=fingerprint_sha256,
                media_type="application/gzip",
            )
        ],
    )

    inspection = inspect_source(lock_path)

    assert inspection.ok is True
    assert len(inspection.files) == 1
    file_result = inspection.files[0]
    assert file_result.matches is True
    assert file_result.actual_size_bytes == len(raw)
    assert file_result.actual_sha256 == fingerprint_sha256
    assert [member.name for member in file_result.tar_members] == ["chunk_0.ndjson"]
    assert file_result.ndjson_sample is not None
    assert file_result.ndjson_sample.member_name == "chunk_0.ndjson"
    assert file_result.ndjson_sample.truncated is False
    assert [record["name"] for record in file_result.ndjson_sample.sample_records] == [
        "Emacs",
        "Linux",
    ]


def test_ndjson_sample_marks_truncated_when_more_lines_exist(tmp_path: Path) -> None:
    snapshot_directory = tmp_path / "snapshot"
    snapshot_directory.mkdir()
    tar_path = snapshot_directory / "chunk_0.tar.gz"
    records = [json.dumps({"identifier": str(i)}).encode() for i in range(10)]
    raw = _make_tar_gz(tar_path, member_name="chunk_0.ndjson", ndjson_lines=records)

    lock_path = _lock_for(
        tmp_path,
        snapshot_directory,
        [
            SourceLockFile(
                relative_path="chunk_0.tar.gz",
                chunk_identifier="chunk_0",
                size_bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),
                media_type="application/gzip",
            )
        ],
    )

    inspection = inspect_source(lock_path, sample_lines=3)

    sample = inspection.files[0].ndjson_sample
    assert sample is not None
    assert len(sample.sample_records) == 3
    assert sample.truncated is True


def test_size_mismatch_is_reported_without_sampling(tmp_path: Path) -> None:
    snapshot_directory = tmp_path / "snapshot"
    snapshot_directory.mkdir()
    tar_path = snapshot_directory / "chunk_0.tar.gz"
    raw = _make_tar_gz(tar_path, member_name="chunk_0.ndjson", ndjson_lines=[b'{"a":1}'])

    lock_path = _lock_for(
        tmp_path,
        snapshot_directory,
        [
            SourceLockFile(
                relative_path="chunk_0.tar.gz",
                chunk_identifier="chunk_0",
                size_bytes=len(raw) + 1,
                sha256=hashlib.sha256(raw).hexdigest(),
                media_type="application/gzip",
            )
        ],
    )

    inspection = inspect_source(lock_path)

    assert inspection.ok is False
    file_result = inspection.files[0]
    assert file_result.matches is False
    assert file_result.tar_members == ()
    assert file_result.ndjson_sample is None


def test_sha256_mismatch_is_reported(tmp_path: Path) -> None:
    snapshot_directory = tmp_path / "snapshot"
    snapshot_directory.mkdir()
    tar_path = snapshot_directory / "chunk_0.tar.gz"
    raw = _make_tar_gz(tar_path, member_name="chunk_0.ndjson", ndjson_lines=[b'{"a":1}'])

    lock_path = _lock_for(
        tmp_path,
        snapshot_directory,
        [
            SourceLockFile(
                relative_path="chunk_0.tar.gz",
                chunk_identifier="chunk_0",
                size_bytes=len(raw),
                sha256="a" * 64,
                media_type="application/gzip",
            )
        ],
    )

    inspection = inspect_source(lock_path)

    assert inspection.ok is False
    assert inspection.files[0].matches is False


def test_symlinked_file_is_resolved_and_inspected(tmp_path: Path) -> None:
    snapshot_directory = tmp_path / "snapshot"
    snapshot_directory.mkdir()
    real_tar = tmp_path / "elsewhere" / "chunk_0.tar.gz"
    real_tar.parent.mkdir()
    raw = _make_tar_gz(real_tar, member_name="chunk_0.ndjson", ndjson_lines=[b'{"a":1}'])
    (snapshot_directory / "chunk_0.tar.gz").symlink_to(real_tar)

    lock_path = _lock_for(
        tmp_path,
        snapshot_directory,
        [
            SourceLockFile(
                relative_path="chunk_0.tar.gz",
                chunk_identifier="chunk_0",
                size_bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),
                media_type="application/gzip",
            )
        ],
    )

    inspection = inspect_source(lock_path)

    assert inspection.ok is True
    assert inspection.files[0].matches is True


def test_missing_referenced_file_raises(tmp_path: Path) -> None:
    snapshot_directory = tmp_path / "snapshot"
    snapshot_directory.mkdir()

    lock_path = _lock_for(
        tmp_path,
        snapshot_directory,
        [
            SourceLockFile(
                relative_path="missing.tar.gz",
                chunk_identifier="chunk_0",
                size_bytes=10,
                sha256="a" * 64,
                media_type="application/gzip",
            )
        ],
    )

    with pytest.raises(InspectError, match="cannot fingerprint"):
        inspect_source(lock_path)


def test_malformed_tar_is_rejected(tmp_path: Path) -> None:
    snapshot_directory = tmp_path / "snapshot"
    snapshot_directory.mkdir()
    fake_tar = snapshot_directory / "chunk_0.tar.gz"
    fake_tar.write_bytes(b"not a real tar.gz file")

    lock_path = _lock_for(
        tmp_path,
        snapshot_directory,
        [
            SourceLockFile(
                relative_path="chunk_0.tar.gz",
                chunk_identifier="chunk_0",
                size_bytes=fake_tar.stat().st_size,
                sha256=hashlib.sha256(fake_tar.read_bytes()).hexdigest(),
                media_type="application/gzip",
            )
        ],
    )

    with pytest.raises(InspectError, match="cannot read tar archive"):
        inspect_source(lock_path)


def test_malformed_ndjson_line_is_rejected(tmp_path: Path) -> None:
    snapshot_directory = tmp_path / "snapshot"
    snapshot_directory.mkdir()
    tar_path = snapshot_directory / "chunk_0.tar.gz"
    raw = _make_tar_gz(tar_path, member_name="chunk_0.ndjson", ndjson_lines=[b"not json at all"])

    lock_path = _lock_for(
        tmp_path,
        snapshot_directory,
        [
            SourceLockFile(
                relative_path="chunk_0.tar.gz",
                chunk_identifier="chunk_0",
                size_bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),
                media_type="application/gzip",
            )
        ],
    )

    with pytest.raises(InspectError, match="invalid NDJSON line"):
        inspect_source(lock_path)


def test_lock_path_must_be_absolute() -> None:
    with pytest.raises(InspectError, match="absolute"):
        inspect_source(Path("relative/source.lock.json"))


def test_lock_path_must_not_be_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.lock.json"
    real.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.lock.json"
    link.symlink_to(real)

    with pytest.raises(InspectError, match="symlink"):
        inspect_source(link)


def test_missing_lock_file_raises(tmp_path: Path) -> None:
    with pytest.raises(InspectError, match="cannot read source lock"):
        inspect_source(tmp_path / "missing.lock.json")


def test_invalid_lock_json_raises(tmp_path: Path) -> None:
    lock_path = tmp_path / "source.lock.json"
    lock_path.write_text("not json", encoding="utf-8")

    with pytest.raises(InspectError, match="invalid source lock"):
        inspect_source(lock_path)


def test_non_positive_sample_lines_is_rejected(tmp_path: Path) -> None:
    lock_path = tmp_path / "source.lock.json"
    lock_path.write_text("{}", encoding="utf-8")

    with pytest.raises(InspectError, match="sample_lines"):
        inspect_source(lock_path, sample_lines=0)


def test_payload_matches_dataclass_fields(tmp_path: Path) -> None:
    snapshot_directory = tmp_path / "snapshot"
    snapshot_directory.mkdir()
    tar_path = snapshot_directory / "chunk_0.tar.gz"
    raw = _make_tar_gz(tar_path, member_name="chunk_0.ndjson", ndjson_lines=[b'{"a":1}'])

    lock_path = _lock_for(
        tmp_path,
        snapshot_directory,
        [
            SourceLockFile(
                relative_path="chunk_0.tar.gz",
                chunk_identifier="chunk_0",
                size_bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),
                media_type="application/gzip",
            )
        ],
    )

    inspection = inspect_source(lock_path)
    payload = inspection.payload()

    assert payload["ok"] is True
    assert payload["snapshot"]["project"] == "jawiki"
    assert payload["files"][0]["chunk_identifier"] == "chunk_0"
