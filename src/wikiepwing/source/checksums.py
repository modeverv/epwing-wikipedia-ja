"""Streaming file fingerprints: bounded-memory SHA-256 and size verification."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

DEFAULT_READ_CHUNK_BYTES = 1 << 20
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class FingerprintError(ValueError):
    """Raised when a file fingerprint cannot be computed or does not match expectations."""


@dataclass(frozen=True, slots=True)
class FileFingerprint:
    """The measured size and SHA-256 of one file, from an actual streaming read."""

    size_bytes: int
    sha256: str


def compute_fingerprint(
    path: Path,
    *,
    read_chunk_bytes: int = DEFAULT_READ_CHUNK_BYTES,
    on_progress: Callable[[int, int], None] | None = None,
) -> FileFingerprint:
    """Stream `path` in bounded chunks and return its measured size and SHA-256."""
    if read_chunk_bytes < 1:
        raise FingerprintError("read_chunk_bytes must be positive")
    if path.is_symlink():
        raise FingerprintError(f"fingerprint target must not be a symlink: {path}")
    hasher = hashlib.sha256()
    size_bytes = 0
    try:
        total_bytes = path.stat().st_size
        with path.open("rb") as file:
            while True:
                block = file.read(read_chunk_bytes)
                if not block:
                    break
                hasher.update(block)
                size_bytes += len(block)
                if on_progress is not None:
                    on_progress(size_bytes, total_bytes)
    except OSError as error:
        raise FingerprintError(f"cannot read fingerprint target {path}: {error}") from error
    return FileFingerprint(size_bytes=size_bytes, sha256=hasher.hexdigest())


def verify_fingerprint(
    path: Path,
    *,
    expected_size_bytes: int,
    expected_sha256: str,
    read_chunk_bytes: int = DEFAULT_READ_CHUNK_BYTES,
    on_progress: Callable[[int, int], None] | None = None,
) -> FileFingerprint:
    """Verify `path` matches an expected size and SHA-256; return the measured fingerprint."""
    if expected_size_bytes < 0:
        raise FingerprintError("expected_size_bytes must not be negative")
    if not _SHA256.fullmatch(expected_sha256):
        raise FingerprintError("expected_sha256 must be 64 lowercase hex characters")
    actual = compute_fingerprint(path, read_chunk_bytes=read_chunk_bytes, on_progress=on_progress)
    if actual.size_bytes != expected_size_bytes:
        raise FingerprintError(
            f"size mismatch for {path}: expected {expected_size_bytes} bytes, "
            f"got {actual.size_bytes} bytes"
        )
    if actual.sha256 != expected_sha256:
        raise FingerprintError(
            f"sha256 mismatch for {path}: expected {expected_sha256}, got {actual.sha256}"
        )
    return actual
