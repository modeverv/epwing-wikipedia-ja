"""Register predownloaded Snapshot files without re-fetching them from the network."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from wikiepwing.source.acquire import PROVIDER, AcquireResult
from wikiepwing.source.checksums import FileFingerprint, compute_fingerprint
from wikiepwing.source.lockfile import (
    SourceLockAcquirer,
    SourceLockFile,
    build_source_lock,
    write_source_lock,
)

CHUNK_MEDIA_TYPE = "application/gzip"


class RegisterError(RuntimeError):
    """Raised when a predownloaded Snapshot file cannot be registered safely."""


@dataclass(frozen=True, slots=True)
class LocalSourceFile:
    """One predownloaded file to register, with an optional known checksum."""

    source_path: Path
    chunk_identifier: str
    expected_sha256: str | None = None


def register_local_source(
    files: Sequence[LocalSourceFile],
    *,
    project: str,
    namespace: int,
    snapshot_identifier: str,
    snapshot_version: str,
    date_modified: datetime,
    sources_root: Path,
    copy: bool = True,
    acquirer_name: str,
    acquirer_version: str,
    acquirer_git_commit: str,
) -> AcquireResult:
    """Register predownloaded files as one Snapshot version, copying or symlinking them in."""
    if not sources_root.is_absolute():
        raise RegisterError(f"sources_root must be an absolute path: {sources_root}")
    if not files:
        raise RegisterError("files must not be empty")

    snapshot_directory = sources_root / project / snapshot_version
    if snapshot_directory.is_symlink():
        raise RegisterError(f"snapshot directory must not be a symlink: {snapshot_directory}")
    snapshot_directory.mkdir(parents=True, exist_ok=True)

    lock_files: list[SourceLockFile] = []
    for file in files:
        _require_non_empty("chunk_identifier", file.chunk_identifier)
        relative_path = f"{file.chunk_identifier}.tar.gz"
        destination = snapshot_directory / relative_path
        fingerprint = _register_one(file, destination, copy=copy)
        lock_files.append(
            SourceLockFile(
                relative_path=relative_path,
                chunk_identifier=file.chunk_identifier,
                size_bytes=fingerprint.size_bytes,
                sha256=fingerprint.sha256,
                media_type=CHUNK_MEDIA_TYPE,
            )
        )

    metadata_response_sha256 = _synthetic_metadata_hash(
        project=project,
        namespace=namespace,
        snapshot_identifier=snapshot_identifier,
        snapshot_version=snapshot_version,
        date_modified=date_modified,
        files=lock_files,
    )
    lock = build_source_lock(
        provider=PROVIDER,
        project=project,
        namespace=namespace,
        snapshot_identifier=snapshot_identifier,
        snapshot_version=snapshot_version,
        date_modified=date_modified,
        downloaded_at=date_modified,
        files=lock_files,
        metadata_response_sha256=metadata_response_sha256,
        acquirer=SourceLockAcquirer(
            name=acquirer_name,
            version=acquirer_version,
            git_commit=acquirer_git_commit,
        ),
    )
    lock_path = snapshot_directory / "source.lock.json"
    write_source_lock(lock, lock_path)
    return AcquireResult(snapshot_directory=snapshot_directory, lock_path=lock_path, lock=lock)


def _register_one(file: LocalSourceFile, destination: Path, *, copy: bool) -> FileFingerprint:
    if destination.is_symlink():
        fingerprint = compute_fingerprint(destination.resolve(strict=True))
    elif destination.is_file():
        fingerprint = compute_fingerprint(destination)
    else:
        resolved_source = _resolve_source_file(file.source_path)
        if copy:
            _copy_atomically(resolved_source, destination)
            fingerprint = compute_fingerprint(destination)
        else:
            destination.symlink_to(resolved_source)
            fingerprint = compute_fingerprint(resolved_source)
    if file.expected_sha256 is not None and fingerprint.sha256 != file.expected_sha256:
        raise RegisterError(
            f"sha256 mismatch for {file.source_path}: "
            f"expected {file.expected_sha256}, got {fingerprint.sha256}"
        )
    return fingerprint


def _resolve_source_file(path: Path) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise RegisterError(f"predownloaded file does not exist: {path}: {error}") from error
    if not resolved.is_file():
        raise RegisterError(f"predownloaded path is not a regular file: {path}")
    return resolved


def _copy_atomically(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", delete=False
    )
    try:
        temp_path = Path(handle.name)
        with source.open("rb") as source_handle:
            shutil.copyfileobj(source_handle, handle, length=1 << 20)
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    os.replace(temp_path, destination)


def _synthetic_metadata_hash(
    *,
    project: str,
    namespace: int,
    snapshot_identifier: str,
    snapshot_version: str,
    date_modified: datetime,
    files: Sequence[SourceLockFile],
) -> str:
    """Hash the registration inputs; there is no Enterprise metadata response to hash instead."""
    payload = {
        "project": project,
        "namespace": namespace,
        "snapshot_identifier": snapshot_identifier,
        "snapshot_version": snapshot_version,
        "date_modified": date_modified.isoformat(),
        "chunk_identifiers": sorted(file.chunk_identifier for file in files),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_non_empty(label: str, value: str) -> None:
    if not value or value != value.strip():
        raise RegisterError(f"{label} must be a non-empty, trimmed string")
