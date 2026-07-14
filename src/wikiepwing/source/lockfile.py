"""source.lock.json model: chunk-aware files, canonical serialization, round-trip parsing."""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

SCHEMA_VERSION = 1
LATEST = "latest"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT = re.compile(r"^[0-9a-f]{4,64}$")


class SourceLockError(ValueError):
    """Raised when a source lock cannot be built, serialized, or parsed safely."""


@dataclass(frozen=True, slots=True)
class SourceLockFile:
    """One downloaded chunk file recorded in a source lock."""

    relative_path: str
    chunk_identifier: str
    size_bytes: int
    sha256: str
    media_type: str

    def payload(self) -> dict[str, object]:
        """Return this file's canonical JSON-serializable representation."""
        return {
            "relative_path": self.relative_path,
            "chunk_identifier": self.chunk_identifier,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "media_type": self.media_type,
        }


@dataclass(frozen=True, slots=True)
class SourceLockAcquirer:
    """The tool build that produced a source lock."""

    name: str
    version: str
    git_commit: str

    def payload(self) -> dict[str, object]:
        """Return this acquirer's canonical JSON-serializable representation."""
        return {"name": self.name, "version": self.version, "git_commit": self.git_commit}


@dataclass(frozen=True, slots=True)
class SourceLock:
    """A fully validated, immutable `source.lock.json` document."""

    schema_version: int
    provider: str
    project: str
    namespace: int
    snapshot_identifier: str
    snapshot_version: str
    date_modified: datetime
    downloaded_at: datetime
    files: tuple[SourceLockFile, ...]
    supplements: tuple[str, ...]
    metadata_response_sha256: str
    acquirer: SourceLockAcquirer

    def payload(self) -> dict[str, object]:
        """Return this lock's canonical JSON-serializable representation."""
        return {
            "schema_version": self.schema_version,
            "provider": self.provider,
            "project": self.project,
            "namespace": self.namespace,
            "snapshot_identifier": self.snapshot_identifier,
            "snapshot_version": self.snapshot_version,
            "date_modified": _format_timestamp(self.date_modified),
            "downloaded_at": _format_timestamp(self.downloaded_at),
            "files": [file.payload() for file in self.files],
            "supplements": list(self.supplements),
            "metadata_response_sha256": self.metadata_response_sha256,
            "acquirer": self.acquirer.payload(),
        }


def build_source_lock(
    *,
    provider: str,
    project: str,
    namespace: int,
    snapshot_identifier: str,
    snapshot_version: str,
    date_modified: datetime,
    downloaded_at: datetime,
    files: Sequence[SourceLockFile],
    supplements: Sequence[str] = (),
    metadata_response_sha256: str,
    acquirer: SourceLockAcquirer,
) -> SourceLock:
    """Validate inputs and construct one immutable source lock document."""
    _require_non_empty("provider", provider)
    _require_non_empty("project", project)
    if namespace < 0:
        raise SourceLockError("namespace must not be negative")
    _require_non_empty("snapshot_identifier", snapshot_identifier)
    _require_non_empty("snapshot_version", snapshot_version)
    if snapshot_version == LATEST:
        raise SourceLockError(f"snapshot_version must be concrete, not {LATEST!r}")
    _require_timezone_aware("date_modified", date_modified)
    _require_timezone_aware("downloaded_at", downloaded_at)
    if not files:
        raise SourceLockError("files must not be empty")
    seen_chunks: set[str] = set()
    seen_paths: set[str] = set()
    for file in files:
        _validate_file(file)
        if file.chunk_identifier in seen_chunks:
            raise SourceLockError(f"duplicate chunk_identifier: {file.chunk_identifier}")
        seen_chunks.add(file.chunk_identifier)
        if file.relative_path in seen_paths:
            raise SourceLockError(f"duplicate relative_path: {file.relative_path}")
        seen_paths.add(file.relative_path)
    for supplement in supplements:
        _require_relative_path("supplements entry", supplement)
    if not _SHA256.fullmatch(metadata_response_sha256):
        raise SourceLockError("metadata_response_sha256 must be 64 lowercase hex characters")
    _validate_acquirer(acquirer)
    return SourceLock(
        schema_version=SCHEMA_VERSION,
        provider=provider,
        project=project,
        namespace=namespace,
        snapshot_identifier=snapshot_identifier,
        snapshot_version=snapshot_version,
        date_modified=date_modified,
        downloaded_at=downloaded_at,
        files=tuple(files),
        supplements=tuple(supplements),
        metadata_response_sha256=metadata_response_sha256,
        acquirer=acquirer,
    )


def canonical_json(lock: SourceLock) -> bytes:
    """Serialize a source lock deterministically: sorted keys, trailing newline."""
    return (json.dumps(lock.payload(), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def write_source_lock(lock: SourceLock, destination: Path) -> None:
    """Atomically write a source lock's canonical JSON to `destination`."""
    payload = canonical_json(lock)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", delete=False
    )
    try:
        temp_path = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    os.replace(temp_path, destination)


def parse_source_lock(raw: bytes) -> SourceLock:
    """Parse and fully validate a `source.lock.json` document."""
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceLockError(f"source lock is not valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise SourceLockError("source lock must be a JSON object")
    fields = cast(dict[str, object], payload)
    schema_version = fields.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise SourceLockError(f"unsupported source lock schema_version: {schema_version!r}")
    files_field = fields.get("files")
    if not isinstance(files_field, list) or not files_field:
        raise SourceLockError("source lock files must be a non-empty JSON array")
    files = tuple(
        _parse_file(entry, index) for index, entry in enumerate(cast(list[object], files_field))
    )
    supplements_field = fields.get("supplements")
    if not isinstance(supplements_field, list) or not all(
        isinstance(item, str) and item for item in cast(list[object], supplements_field)
    ):
        raise SourceLockError("source lock supplements must be a JSON array of non-empty strings")
    acquirer_field = fields.get("acquirer")
    if not isinstance(acquirer_field, dict):
        raise SourceLockError("source lock acquirer must be a JSON object")
    acquirer = _parse_acquirer(cast(dict[str, object], acquirer_field))
    return build_source_lock(
        provider=_require_field_string(fields, "provider"),
        project=_require_field_string(fields, "project"),
        namespace=_require_field_int(fields, "namespace"),
        snapshot_identifier=_require_field_string(fields, "snapshot_identifier"),
        snapshot_version=_require_field_string(fields, "snapshot_version"),
        date_modified=_require_field_datetime(fields, "date_modified"),
        downloaded_at=_require_field_datetime(fields, "downloaded_at"),
        files=files,
        supplements=cast(list[str], supplements_field),
        metadata_response_sha256=_require_field_string(fields, "metadata_response_sha256"),
        acquirer=acquirer,
    )


def _validate_file(file: SourceLockFile) -> None:
    _require_relative_path("files entry relative_path", file.relative_path)
    _require_non_empty("files entry chunk_identifier", file.chunk_identifier)
    if file.size_bytes < 0:
        raise SourceLockError("files entry size_bytes must not be negative")
    if not _SHA256.fullmatch(file.sha256):
        raise SourceLockError("files entry sha256 must be 64 lowercase hex characters")
    _require_non_empty("files entry media_type", file.media_type)


def _validate_acquirer(acquirer: SourceLockAcquirer) -> None:
    _require_non_empty("acquirer.name", acquirer.name)
    _require_non_empty("acquirer.version", acquirer.version)
    if not _GIT_COMMIT.fullmatch(acquirer.git_commit):
        raise SourceLockError("acquirer.git_commit must be 4-64 lowercase hex characters")


def _require_relative_path(label: str, path: str) -> None:
    if not path or path.startswith("/") or path != path.strip():
        raise SourceLockError(f"{label} must be a non-empty relative path: {path!r}")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise SourceLockError(f"{label} must not contain '.' or '..' segments: {path!r}")


def _require_non_empty(label: str, value: str) -> None:
    if not value or value != value.strip():
        raise SourceLockError(f"{label} must be a non-empty, trimmed string")


def _require_timezone_aware(label: str, value: datetime) -> None:
    if value.tzinfo is None:
        raise SourceLockError(f"{label} must be timezone-aware")


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_file(entry: object, index: int) -> SourceLockFile:
    if not isinstance(entry, dict):
        raise SourceLockError(f"files entry {index} must be a JSON object")
    fields = cast(dict[str, object], entry)
    return SourceLockFile(
        relative_path=_require_field_string(fields, "relative_path"),
        chunk_identifier=_require_field_string(fields, "chunk_identifier"),
        size_bytes=_require_field_int(fields, "size_bytes"),
        sha256=_require_field_string(fields, "sha256"),
        media_type=_require_field_string(fields, "media_type"),
    )


def _parse_acquirer(fields: dict[str, object]) -> SourceLockAcquirer:
    return SourceLockAcquirer(
        name=_require_field_string(fields, "name"),
        version=_require_field_string(fields, "version"),
        git_commit=_require_field_string(fields, "git_commit"),
    )


def _require_field_string(fields: dict[str, object], key: str) -> str:
    value = fields.get(key)
    if not isinstance(value, str) or not value:
        raise SourceLockError(f"source lock is missing a non-empty string field: {key}")
    return value


def _require_field_int(fields: dict[str, object], key: str) -> int:
    value = fields.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SourceLockError(f"source lock is missing an integer field: {key}")
    return value


def _require_field_datetime(fields: dict[str, object], key: str) -> datetime:
    value = fields.get(key)
    if not isinstance(value, str):
        raise SourceLockError(f"source lock is missing a string field: {key}")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise SourceLockError(
            f"source lock field {key} is not a valid timestamp: {error}"
        ) from error
    if parsed.tzinfo is None:
        raise SourceLockError(f"source lock field {key} must include a timezone")
    return parsed
