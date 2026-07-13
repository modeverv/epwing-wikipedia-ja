"""Snapshot metadata: project/namespace filtering, concrete version resolution."""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

DEFAULT_METADATA_TIMEOUT_SECONDS = 30.0
MAX_METADATA_RESPONSE_BYTES = 4 * 1024 * 1024
LATEST = "latest"


class SnapshotMetadataError(RuntimeError):
    """Raised when Snapshot metadata cannot be listed, filtered, or resolved safely."""


@dataclass(frozen=True, slots=True)
class SnapshotCandidate:
    """One Snapshot metadata entry as enumerated by the Enterprise API."""

    identifier: str
    project: str
    namespace: int
    version_identifier: str
    date_modified: datetime
    size_bytes: int | None


@dataclass(frozen=True, slots=True)
class ResolvedSnapshot:
    """A single concrete Snapshot selected for one project/namespace pair."""

    project: str
    namespace: int
    snapshot_identifier: str
    version_identifier: str
    date_modified: datetime
    size_bytes: int | None
    metadata_response_sha256: str


class SnapshotMetadataTransport(Protocol):
    """Network operation required to enumerate Snapshot metadata."""

    def list_snapshots(self, access_token: str, *, timeout_seconds: float) -> bytes: ...


class SnapshotMetadataClient:
    """Filter enumerated Snapshot metadata to one project/namespace and resolve a version."""

    def __init__(
        self,
        transport: SnapshotMetadataTransport,
        *,
        timeout_seconds: float = DEFAULT_METADATA_TIMEOUT_SECONDS,
    ) -> None:
        if timeout_seconds <= 0:
            raise SnapshotMetadataError("metadata timeout_seconds must be positive")
        self._transport = transport
        self._timeout_seconds = timeout_seconds

    def resolve(
        self,
        access_token: str,
        *,
        project: str,
        namespace: int,
        requested_version: str,
    ) -> ResolvedSnapshot:
        """Enumerate Snapshots, filter to project/namespace, and resolve one concrete version."""
        raw = self._transport.list_snapshots(access_token, timeout_seconds=self._timeout_seconds)
        if len(raw) > MAX_METADATA_RESPONSE_BYTES:
            raise SnapshotMetadataError(
                f"Snapshot metadata response exceeded {MAX_METADATA_RESPONSE_BYTES} bytes"
            )
        candidates = _parse_snapshot_list(raw)
        matches = [
            candidate
            for candidate in candidates
            if candidate.project == project and candidate.namespace == namespace
        ]
        if not matches:
            raise SnapshotMetadataError(
                f"no Snapshot listed for project={project!r} namespace={namespace}"
            )
        chosen = _select_version(matches, requested_version)
        return ResolvedSnapshot(
            project=chosen.project,
            namespace=chosen.namespace,
            snapshot_identifier=chosen.identifier,
            version_identifier=chosen.version_identifier,
            date_modified=chosen.date_modified,
            size_bytes=chosen.size_bytes,
            metadata_response_sha256=hashlib.sha256(raw).hexdigest(),
        )


def _select_version(matches: list[SnapshotCandidate], requested_version: str) -> SnapshotCandidate:
    if not requested_version or requested_version != requested_version.strip():
        raise SnapshotMetadataError("requested_version must be a non-empty trimmed string")
    if requested_version == LATEST:
        return max(
            matches,
            key=lambda candidate: (candidate.date_modified, candidate.version_identifier),
        )
    found = [
        candidate for candidate in matches if candidate.version_identifier == requested_version
    ]
    if not found:
        raise SnapshotMetadataError(f"requested Snapshot version not found: {requested_version}")
    if len(found) > 1:
        raise SnapshotMetadataError(
            f"multiple Snapshots share version identifier: {requested_version}"
        )
    return found[0]


def _parse_snapshot_list(raw: bytes) -> tuple[SnapshotCandidate, ...]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SnapshotMetadataError(
            f"Snapshot metadata response was not valid JSON: {error}"
        ) from error
    if not isinstance(payload, list):
        raise SnapshotMetadataError("Snapshot metadata response must be a JSON array")
    candidates = tuple(
        _parse_snapshot_entry(entry, index)
        for index, entry in enumerate(cast(list[object], payload))
    )
    if not candidates:
        raise SnapshotMetadataError("Snapshot metadata response listed zero snapshots")
    return candidates


def _parse_snapshot_entry(entry: object, index: int) -> SnapshotCandidate:
    if not isinstance(entry, dict):
        raise SnapshotMetadataError(f"Snapshot metadata entry {index} must be a JSON object")
    fields = cast(dict[str, object], entry)
    identifier = _require_string(fields, "identifier", index)
    project = _require_string(
        _require_object(fields, "project", index), "identifier", index, "project.identifier"
    )
    namespace = _require_int(
        _require_object(fields, "namespace", index), "identifier", index, "namespace.identifier"
    )
    version_identifier = _require_string(fields, "version", index)
    if version_identifier == LATEST:
        raise SnapshotMetadataError(
            f"Snapshot metadata entry {index} has non-concrete version: {LATEST!r}"
        )
    date_modified = _require_datetime(fields, "date_modified", index)
    size_bytes = fields.get("size")
    if size_bytes is not None and (
        isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0
    ):
        raise SnapshotMetadataError(f"Snapshot metadata entry {index} has an invalid size")
    return SnapshotCandidate(
        identifier=identifier,
        project=project,
        namespace=namespace,
        version_identifier=version_identifier,
        date_modified=date_modified,
        size_bytes=size_bytes,
    )


def _require_object(fields: dict[str, object], key: str, index: int) -> dict[str, object]:
    value = fields.get(key)
    if not isinstance(value, dict):
        raise SnapshotMetadataError(
            f"Snapshot metadata entry {index} is missing object field: {key}"
        )
    return cast(dict[str, object], value)


def _require_string(
    fields: dict[str, object], key: str, index: int, path: str | None = None
) -> str:
    value = fields.get(key)
    if not isinstance(value, str) or not value:
        raise SnapshotMetadataError(
            f"Snapshot metadata entry {index} is missing a non-empty string field: {path or key}"
        )
    return value


def _require_int(fields: dict[str, object], key: str, index: int, path: str | None = None) -> int:
    value = fields.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SnapshotMetadataError(
            f"Snapshot metadata entry {index} is missing an integer field: {path or key}"
        )
    return value


def _require_datetime(fields: dict[str, object], key: str, index: int) -> datetime:
    value = fields.get(key)
    if not isinstance(value, str):
        raise SnapshotMetadataError(
            f"Snapshot metadata entry {index} is missing string field: {key}"
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise SnapshotMetadataError(
            f"Snapshot metadata entry {index} has an invalid {key}: {error}"
        ) from error
    if parsed.tzinfo is None:
        raise SnapshotMetadataError(
            f"Snapshot metadata entry {index} {key} must include a timezone"
        )
    return parsed


class _MetadataResponse(Protocol):
    """The subset of an HTTP response this transport relies on."""

    status: int

    def read(self, limit: int) -> bytes: ...


class HttpSnapshotMetadataTransport:
    """Bounded HTTPS transport for the Wikimedia Enterprise Snapshot metadata API."""

    def __init__(
        self,
        base_url: str,
        *,
        opener: Callable[..., AbstractContextManager[_MetadataResponse]] = urllib.request.urlopen,
    ) -> None:
        if not base_url.startswith("https://"):
            raise SnapshotMetadataError("Snapshot metadata base URL must use https://")
        self._base_url = base_url.rstrip("/")
        self._opener = opener

    def list_snapshots(self, access_token: str, *, timeout_seconds: float) -> bytes:
        """Fetch the raw Snapshot metadata listing for the configured base URL."""
        if timeout_seconds <= 0:
            raise SnapshotMetadataError("metadata timeout_seconds must be positive")
        if not access_token:
            raise SnapshotMetadataError("access_token must not be empty")
        request = urllib.request.Request(
            f"{self._base_url}/snapshots",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with self._opener(request, timeout=timeout_seconds) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read(MAX_METADATA_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise SnapshotMetadataError(
                    f"Snapshot metadata request was rejected: HTTP {error.code}"
                ) from error
            raise SnapshotMetadataError(
                f"Snapshot metadata request failed: HTTP {error.code}"
            ) from error
        except urllib.error.URLError as error:
            raise SnapshotMetadataError(
                f"Snapshot metadata request failed: {error.reason}"
            ) from error
        except TimeoutError as error:
            raise SnapshotMetadataError(
                f"Snapshot metadata request timed out after {timeout_seconds:g} seconds"
            ) from error
        if len(raw) > MAX_METADATA_RESPONSE_BYTES:
            raise SnapshotMetadataError(
                f"Snapshot metadata response exceeded {MAX_METADATA_RESPONSE_BYTES} bytes"
            )
        if status >= 400:
            raise SnapshotMetadataError(f"Snapshot metadata request failed: HTTP {status}")
        return raw
