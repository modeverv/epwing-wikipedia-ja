"""Inspect an acquired Snapshot: lock re-verification, tar listing, NDJSON preview."""

from __future__ import annotations

import json
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import IO, cast

from wikiepwing.source.checksums import FingerprintError, compute_fingerprint
from wikiepwing.source.lockfile import (
    SourceLock,
    SourceLockError,
    SourceLockFile,
    parse_source_lock,
)

DEFAULT_SAMPLE_LINES = 5
MAX_SAMPLE_LINE_BYTES = 65536


class InspectError(RuntimeError):
    """Raised when a Snapshot source cannot be inspected safely."""


@dataclass(frozen=True, slots=True)
class TarMember:
    """One regular-file member found inside a chunk's tar.gz archive."""

    name: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class NdjsonSample:
    """A bounded preview of the NDJSON content inside one chunk archive."""

    member_name: str
    sample_records: tuple[dict[str, object], ...]
    truncated: bool


@dataclass(frozen=True, slots=True)
class FileInspection:
    """The inspection outcome for one file recorded in a source lock."""

    relative_path: str
    chunk_identifier: str
    recorded_size_bytes: int
    recorded_sha256: str
    actual_size_bytes: int
    actual_sha256: str
    matches: bool
    tar_members: tuple[TarMember, ...]
    ndjson_sample: NdjsonSample | None

    def payload(self) -> dict[str, object]:
        """Return this file's JSON-serializable inspection summary."""
        return {
            "relative_path": self.relative_path,
            "chunk_identifier": self.chunk_identifier,
            "recorded_size_bytes": self.recorded_size_bytes,
            "recorded_sha256": self.recorded_sha256,
            "actual_size_bytes": self.actual_size_bytes,
            "actual_sha256": self.actual_sha256,
            "matches": self.matches,
            "tar_members": [
                {"name": member.name, "size_bytes": member.size_bytes}
                for member in self.tar_members
            ],
            "ndjson_sample": (
                None
                if self.ndjson_sample is None
                else {
                    "member_name": self.ndjson_sample.member_name,
                    "sample_records": list(self.ndjson_sample.sample_records),
                    "truncated": self.ndjson_sample.truncated,
                }
            ),
        }


@dataclass(frozen=True, slots=True)
class SourceInspection:
    """The full inspection outcome for one source.lock.json and its files."""

    lock_path: Path
    lock: SourceLock
    files: tuple[FileInspection, ...]

    @property
    def ok(self) -> bool:
        """Return True only if every recorded file's fingerprint matched."""
        return all(file.matches for file in self.files)

    def payload(self) -> dict[str, object]:
        """Return a JSON-serializable summary of this inspection."""
        return {
            "lock_path": str(self.lock_path),
            "ok": self.ok,
            "snapshot": {
                "project": self.lock.project,
                "namespace": self.lock.namespace,
                "snapshot_identifier": self.lock.snapshot_identifier,
                "snapshot_version": self.lock.snapshot_version,
            },
            "files": [file.payload() for file in self.files],
        }


def inspect_source(
    lock_path: Path, *, sample_lines: int = DEFAULT_SAMPLE_LINES
) -> SourceInspection:
    """Load a source.lock.json, verify each file, and sample its tar/NDJSON contents."""
    if sample_lines < 1:
        raise InspectError("sample_lines must be positive")
    if not lock_path.is_absolute():
        raise InspectError(f"lock_path must be an absolute path: {lock_path}")
    if lock_path.is_symlink():
        raise InspectError(f"lock_path must not be a symlink: {lock_path}")
    try:
        raw = lock_path.read_bytes()
    except OSError as error:
        raise InspectError(f"cannot read source lock: {lock_path}: {error}") from error
    try:
        lock = parse_source_lock(raw)
    except SourceLockError as error:
        raise InspectError(f"invalid source lock: {error}") from error

    snapshot_directory = lock_path.parent
    files = tuple(_inspect_file(snapshot_directory, file, sample_lines) for file in lock.files)
    return SourceInspection(lock_path=lock_path, lock=lock, files=files)


def _inspect_file(
    snapshot_directory: Path, file: SourceLockFile, sample_lines: int
) -> FileInspection:
    path = snapshot_directory / file.relative_path
    real_path = path.resolve(strict=True) if path.is_symlink() else path
    try:
        fingerprint = compute_fingerprint(real_path)
    except FingerprintError as error:
        raise InspectError(f"cannot fingerprint {path}: {error}") from error

    matches = fingerprint.size_bytes == file.size_bytes and fingerprint.sha256 == file.sha256
    tar_members: tuple[TarMember, ...] = ()
    ndjson_sample: NdjsonSample | None = None
    if matches:
        tar_members, ndjson_sample = _sample_tar(real_path, sample_lines)

    return FileInspection(
        relative_path=file.relative_path,
        chunk_identifier=file.chunk_identifier,
        recorded_size_bytes=file.size_bytes,
        recorded_sha256=file.sha256,
        actual_size_bytes=fingerprint.size_bytes,
        actual_sha256=fingerprint.sha256,
        matches=matches,
        tar_members=tar_members,
        ndjson_sample=ndjson_sample,
    )


def _sample_tar(path: Path, sample_lines: int) -> tuple[tuple[TarMember, ...], NdjsonSample | None]:
    try:
        with tarfile.open(path, mode="r:gz") as archive:
            members = tuple(
                TarMember(name=member.name, size_bytes=member.size)
                for member in archive.getmembers()
                if member.isfile()
            )
            ndjson_member_name = next(
                (member.name for member in members if member.name.endswith(".ndjson")), None
            )
            ndjson_sample = None
            if ndjson_member_name is not None:
                extracted = archive.extractfile(ndjson_member_name)
                if extracted is None:
                    raise InspectError(f"cannot read tar member: {ndjson_member_name}")
                ndjson_sample = _sample_ndjson(extracted, ndjson_member_name, sample_lines)
    except tarfile.TarError as error:
        raise InspectError(f"cannot read tar archive {path}: {error}") from error
    return members, ndjson_sample


def _sample_ndjson(stream: IO[bytes], member_name: str, sample_lines: int) -> NdjsonSample:
    records: list[dict[str, object]] = []
    while len(records) < sample_lines:
        raw_line = stream.readline(MAX_SAMPLE_LINE_BYTES + 1)
        if not raw_line:
            return NdjsonSample(
                member_name=member_name, sample_records=tuple(records), truncated=False
            )
        if len(raw_line) > MAX_SAMPLE_LINE_BYTES:
            raise InspectError(
                f"NDJSON line exceeded {MAX_SAMPLE_LINE_BYTES} bytes in {member_name}"
            )
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            record = json.loads(stripped)
        except json.JSONDecodeError as error:
            raise InspectError(f"invalid NDJSON line in {member_name}: {error}") from error
        if not isinstance(record, dict):
            raise InspectError(f"NDJSON line in {member_name} is not a JSON object")
        records.append(cast(dict[str, object], record))
    truncated = bool(stream.readline(1))
    return NdjsonSample(member_name=member_name, sample_records=tuple(records), truncated=truncated)
