from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.source.register import (
    LocalSourceFile,
    RegisterError,
    register_local_source,
)

DATE_MODIFIED = datetime(2026, 7, 1, 0, 0, 0, tzinfo=UTC)


def _register(files: list[LocalSourceFile], tmp_path: Path, *, copy: bool = True) -> Path:
    result = register_local_source(
        files,
        project="jawiki",
        namespace=0,
        snapshot_identifier="jawiki_namespace_0",
        snapshot_version="local-2026-07-01",
        date_modified=DATE_MODIFIED,
        sources_root=tmp_path / "sources",
        copy=copy,
        acquirer_name="wikiepwing",
        acquirer_version="0.1.0",
        acquirer_git_commit="abc1234",
    )
    return result.lock_path


def test_copies_predownloaded_file_and_writes_lock(tmp_path: Path) -> None:
    content = b"predownloaded tar.gz bytes"
    source = tmp_path / "downloads" / "mine.tar.gz"
    source.parent.mkdir()
    source.write_bytes(content)

    lock_path = _register(
        [LocalSourceFile(source_path=source, chunk_identifier="jawiki_namespace_0_chunk_0")],
        tmp_path,
    )

    snapshot_dir = tmp_path / "sources" / "jawiki" / "local-2026-07-01"
    registered = snapshot_dir / "jawiki_namespace_0_chunk_0.tar.gz"
    assert registered.is_file()
    assert not registered.is_symlink()
    assert registered.read_bytes() == content
    # original file is untouched and independent of the copy
    assert source.read_bytes() == content

    on_disk = json.loads(lock_path.read_bytes())
    assert on_disk["provider"] == "wikimedia-enterprise-snapshot"
    assert on_disk["snapshot_version"] == "local-2026-07-01"
    assert on_disk["files"][0]["sha256"] == hashlib.sha256(content).hexdigest()
    assert on_disk["files"][0]["relative_path"] == "jawiki_namespace_0_chunk_0.tar.gz"


def test_symlinks_predownloaded_file_when_copy_is_false(tmp_path: Path) -> None:
    content = b"large predownloaded content"
    source = tmp_path / "downloads" / "mine.tar.gz"
    source.parent.mkdir()
    source.write_bytes(content)

    lock_path = _register(
        [LocalSourceFile(source_path=source, chunk_identifier="jawiki_namespace_0_chunk_0")],
        tmp_path,
        copy=False,
    )

    snapshot_dir = tmp_path / "sources" / "jawiki" / "local-2026-07-01"
    registered = snapshot_dir / "jawiki_namespace_0_chunk_0.tar.gz"
    assert registered.is_symlink()
    assert registered.resolve() == source.resolve()
    assert registered.read_bytes() == content

    on_disk = json.loads(lock_path.read_bytes())
    assert on_disk["files"][0]["sha256"] == hashlib.sha256(content).hexdigest()


def test_multiple_files_register_in_order(tmp_path: Path) -> None:
    files = []
    for index in range(3):
        source = tmp_path / "downloads" / f"chunk_{index}.tar.gz"
        source.parent.mkdir(exist_ok=True)
        source.write_bytes(f"content-{index}".encode())
        files.append(
            LocalSourceFile(
                source_path=source, chunk_identifier=f"jawiki_namespace_0_chunk_{index}"
            )
        )

    lock_path = _register(files, tmp_path)

    on_disk = json.loads(lock_path.read_bytes())
    identifiers = [entry["chunk_identifier"] for entry in on_disk["files"]]
    assert identifiers == [
        "jawiki_namespace_0_chunk_0",
        "jawiki_namespace_0_chunk_1",
        "jawiki_namespace_0_chunk_2",
    ]


def test_already_registered_file_is_not_recopied(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "sources" / "jawiki" / "local-2026-07-01"
    snapshot_dir.mkdir(parents=True)
    existing_content = b"already registered"
    (snapshot_dir / "jawiki_namespace_0_chunk_0.tar.gz").write_bytes(existing_content)

    source = tmp_path / "downloads" / "would-overwrite.tar.gz"
    source.parent.mkdir()
    source.write_bytes(b"different bytes that must not be used")

    lock_path = _register(
        [LocalSourceFile(source_path=source, chunk_identifier="jawiki_namespace_0_chunk_0")],
        tmp_path,
    )

    assert (snapshot_dir / "jawiki_namespace_0_chunk_0.tar.gz").read_bytes() == existing_content
    on_disk = json.loads(lock_path.read_bytes())
    assert on_disk["files"][0]["sha256"] == hashlib.sha256(existing_content).hexdigest()


def test_matching_expected_sha256_succeeds(tmp_path: Path) -> None:
    content = b"trusted content"
    source = tmp_path / "downloads" / "mine.tar.gz"
    source.parent.mkdir()
    source.write_bytes(content)

    _register(
        [
            LocalSourceFile(
                source_path=source,
                chunk_identifier="jawiki_namespace_0_chunk_0",
                expected_sha256=hashlib.sha256(content).hexdigest(),
            )
        ],
        tmp_path,
    )


def test_mismatched_expected_sha256_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "downloads" / "mine.tar.gz"
    source.parent.mkdir()
    source.write_bytes(b"actual content")

    with pytest.raises(RegisterError, match="sha256 mismatch"):
        _register(
            [
                LocalSourceFile(
                    source_path=source,
                    chunk_identifier="jawiki_namespace_0_chunk_0",
                    expected_sha256="a" * 64,
                )
            ],
            tmp_path,
        )


def test_missing_predownloaded_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(RegisterError, match="does not exist"):
        _register(
            [
                LocalSourceFile(
                    source_path=tmp_path / "missing.tar.gz",
                    chunk_identifier="jawiki_namespace_0_chunk_0",
                )
            ],
            tmp_path,
        )


def test_directory_as_source_path_is_rejected(tmp_path: Path) -> None:
    directory = tmp_path / "not-a-file"
    directory.mkdir()

    with pytest.raises(RegisterError, match="not a regular file"):
        _register(
            [LocalSourceFile(source_path=directory, chunk_identifier="jawiki_namespace_0_chunk_0")],
            tmp_path,
        )


def test_empty_files_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(RegisterError, match="must not be empty"):
        _register([], tmp_path)


def test_sources_root_must_be_absolute() -> None:
    with pytest.raises(RegisterError, match="absolute"):
        register_local_source(
            [LocalSourceFile(source_path=Path("x"), chunk_identifier="c0")],
            project="jawiki",
            namespace=0,
            snapshot_identifier="jawiki_namespace_0",
            snapshot_version="local-2026-07-01",
            date_modified=DATE_MODIFIED,
            sources_root=Path("relative/sources"),
            acquirer_name="wikiepwing",
            acquirer_version="0.1.0",
            acquirer_git_commit="abc1234",
        )


def test_snapshot_directory_symlink_is_rejected(tmp_path: Path) -> None:
    sources_root = tmp_path / "sources"
    (sources_root / "jawiki").mkdir(parents=True)
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (sources_root / "jawiki" / "local-2026-07-01").symlink_to(real_dir)

    with pytest.raises(RegisterError, match="symlink"):
        register_local_source(
            [LocalSourceFile(source_path=tmp_path / "x", chunk_identifier="c0")],
            project="jawiki",
            namespace=0,
            snapshot_identifier="jawiki_namespace_0",
            snapshot_version="local-2026-07-01",
            date_modified=DATE_MODIFIED,
            sources_root=sources_root,
            acquirer_name="wikiepwing",
            acquirer_version="0.1.0",
            acquirer_git_commit="abc1234",
        )


def test_metadata_response_sha256_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "downloads" / "mine.tar.gz"
    source.parent.mkdir()
    source.write_bytes(b"content")

    lock_path_1 = _register(
        [LocalSourceFile(source_path=source, chunk_identifier="jawiki_namespace_0_chunk_0")],
        tmp_path,
    )
    hash_1 = json.loads(lock_path_1.read_bytes())["metadata_response_sha256"]

    other_root = tmp_path / "other"
    result = register_local_source(
        [LocalSourceFile(source_path=source, chunk_identifier="jawiki_namespace_0_chunk_0")],
        project="jawiki",
        namespace=0,
        snapshot_identifier="jawiki_namespace_0",
        snapshot_version="local-2026-07-01",
        date_modified=DATE_MODIFIED,
        sources_root=other_root,
        acquirer_name="wikiepwing",
        acquirer_version="0.1.0",
        acquirer_git_commit="abc1234",
    )
    hash_2 = json.loads(result.lock_path.read_bytes())["metadata_response_sha256"]

    assert hash_1 == hash_2
