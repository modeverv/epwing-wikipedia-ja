from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from wikiepwing.source.checksums import (
    FingerprintError,
    compute_fingerprint,
    verify_fingerprint,
)


def test_computes_size_and_sha256_for_small_file(tmp_path: Path) -> None:
    content = b"hello world"
    path = tmp_path / "file.bin"
    path.write_bytes(content)

    fingerprint = compute_fingerprint(path)

    assert fingerprint.size_bytes == len(content)
    assert fingerprint.sha256 == hashlib.sha256(content).hexdigest()


def test_computes_fingerprint_for_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")

    fingerprint = compute_fingerprint(path)

    assert fingerprint.size_bytes == 0
    assert fingerprint.sha256 == hashlib.sha256(b"").hexdigest()


def test_computes_fingerprint_streaming_across_multiple_chunks(tmp_path: Path) -> None:
    content = b"x" * 10_000
    path = tmp_path / "large.bin"
    path.write_bytes(content)

    fingerprint = compute_fingerprint(path, read_chunk_bytes=1024)

    assert fingerprint.size_bytes == len(content)
    assert fingerprint.sha256 == hashlib.sha256(content).hexdigest()


def test_reports_streaming_fingerprint_byte_progress(tmp_path: Path) -> None:
    content = b"x" * 10
    path = tmp_path / "progress.bin"
    path.write_bytes(content)
    reports: list[tuple[int, int]] = []

    compute_fingerprint(
        path,
        read_chunk_bytes=4,
        on_progress=lambda done, total: reports.append((done, total)),
    )

    assert reports == [(4, 10), (8, 10), (10, 10)]


def test_rejects_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.bin"
    real.write_bytes(b"data")
    link = tmp_path / "link.bin"
    link.symlink_to(real)

    with pytest.raises(FingerprintError, match="symlink"):
        compute_fingerprint(link)


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FingerprintError, match="cannot read"):
        compute_fingerprint(tmp_path / "missing.bin")


def test_rejects_non_positive_read_chunk_bytes(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"data")

    with pytest.raises(FingerprintError, match="read_chunk_bytes"):
        compute_fingerprint(path, read_chunk_bytes=0)


def test_verify_fingerprint_succeeds_on_match(tmp_path: Path) -> None:
    content = b"verified content"
    path = tmp_path / "file.bin"
    path.write_bytes(content)

    fingerprint = verify_fingerprint(
        path,
        expected_size_bytes=len(content),
        expected_sha256=hashlib.sha256(content).hexdigest(),
    )

    assert fingerprint.size_bytes == len(content)


def test_verify_fingerprint_rejects_size_mismatch(tmp_path: Path) -> None:
    content = b"actual content"
    path = tmp_path / "file.bin"
    path.write_bytes(content)

    with pytest.raises(FingerprintError, match="size mismatch"):
        verify_fingerprint(
            path,
            expected_size_bytes=len(content) + 1,
            expected_sha256=hashlib.sha256(content).hexdigest(),
        )


def test_verify_fingerprint_rejects_sha256_mismatch(tmp_path: Path) -> None:
    content = b"actual content"
    path = tmp_path / "file.bin"
    path.write_bytes(content)

    with pytest.raises(FingerprintError, match="sha256 mismatch"):
        verify_fingerprint(
            path,
            expected_size_bytes=len(content),
            expected_sha256="a" * 64,
        )


def test_verify_fingerprint_rejects_malformed_expected_sha256(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"data")

    with pytest.raises(FingerprintError, match="64 lowercase hex"):
        verify_fingerprint(path, expected_size_bytes=4, expected_sha256="not-hex")


def test_verify_fingerprint_rejects_negative_expected_size(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"data")

    with pytest.raises(FingerprintError, match="expected_size_bytes"):
        verify_fingerprint(path, expected_size_bytes=-1, expected_sha256="a" * 64)
