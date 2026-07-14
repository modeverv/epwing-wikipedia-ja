from __future__ import annotations

import hashlib
import json
import urllib.error
from typing import Any

import pytest

from wikiepwing.source.enterprise import (
    HttpSnapshotMetadataTransport,
    SnapshotMetadataClient,
    SnapshotMetadataError,
)

_UNSET = object()


def _entry(
    *,
    identifier: str = "jawiki_namespace_0",
    project: str = "jawiki",
    namespace: int = 0,
    version: str = "35061ecbd3bc55c31cffd4b46838673d",
    date_modified: str = "2026-07-01T00:50:43.412259882Z",
    size: dict[str, Any] | None | object = _UNSET,
    chunks: list[str] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "identifier": identifier,
        "is_part_of": {"identifier": project},
        "namespace": {"identifier": namespace},
        "version": version,
        "date_modified": date_modified,
        "chunks": chunks if chunks is not None else [f"{identifier}_chunk_0"],
    }
    resolved_size = {"value": 30896.145, "unit_text": "MB"} if size is _UNSET else size
    if resolved_size is not None:
        entry["size"] = resolved_size
    return entry


class _FixedTransport:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw
        self.calls: list[tuple[str, float]] = []

    def list_snapshots(self, access_token: str, *, timeout_seconds: float) -> bytes:
        self.calls.append((access_token, timeout_seconds))
        return self.raw


def _raw(entries: list[dict[str, Any]]) -> bytes:
    return json.dumps(entries).encode("utf-8")


def test_resolves_latest_by_max_date_modified() -> None:
    entries = [
        _entry(version="version-old", date_modified="2026-06-01T00:00:00Z"),
        _entry(version="version-new", date_modified="2026-07-01T00:00:00Z"),
    ]
    raw = _raw(entries)
    client = SnapshotMetadataClient(_FixedTransport(raw))

    resolved = client.resolve("token", project="jawiki", namespace=0, requested_version="latest")

    assert resolved.version_identifier == "version-new"
    assert resolved.snapshot_identifier == "jawiki_namespace_0"
    assert resolved.project == "jawiki"
    assert resolved.namespace == 0
    assert resolved.size_estimate is not None
    assert resolved.size_estimate.value == 30896.145
    assert resolved.size_estimate.unit_text == "MB"
    assert resolved.chunk_identifiers == ("jawiki_namespace_0_chunk_0",)
    assert resolved.metadata_response_sha256 == hashlib.sha256(raw).hexdigest()


def test_resolves_explicit_version() -> None:
    entries = [
        _entry(version="2026-06-01T00:00:00Z", date_modified="2026-06-01T00:00:00Z"),
        _entry(version="2026-07-01T00:00:00Z", date_modified="2026-07-01T00:00:00Z"),
    ]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    resolved = client.resolve(
        "token",
        project="jawiki",
        namespace=0,
        requested_version="2026-06-01T00:00:00Z",
    )

    assert resolved.version_identifier == "2026-06-01T00:00:00Z"


def test_never_returns_latest_as_version_identifier() -> None:
    entries = [_entry(version="2026-07-01T00:00:00Z", date_modified="2026-07-01T00:00:00Z")]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    resolved = client.resolve("token", project="jawiki", namespace=0, requested_version="latest")

    assert resolved.version_identifier != "latest"


def test_missing_explicit_version_raises() -> None:
    entries = [_entry(version="2026-07-01T00:00:00Z")]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    with pytest.raises(SnapshotMetadataError, match="not found"):
        client.resolve(
            "token", project="jawiki", namespace=0, requested_version="2099-01-01T00:00:00Z"
        )


def test_no_matching_project_namespace_raises() -> None:
    entries = [_entry(project="enwiki")]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    with pytest.raises(SnapshotMetadataError, match="no Snapshot listed"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_namespace_mismatch_raises() -> None:
    entries = [_entry(namespace=1)]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    with pytest.raises(SnapshotMetadataError, match="no Snapshot listed"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_entry_with_literal_latest_version_is_rejected() -> None:
    entries = [_entry(version="latest")]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    with pytest.raises(SnapshotMetadataError, match="non-concrete version"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_naive_date_modified_is_rejected() -> None:
    entries = [_entry(date_modified="2026-07-01T00:00:00")]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    with pytest.raises(SnapshotMetadataError, match="timezone"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_missing_size_is_accepted_as_none() -> None:
    entries = [_entry(size=None)]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    resolved = client.resolve("token", project="jawiki", namespace=0, requested_version="latest")

    assert resolved.size_estimate is None


def test_size_missing_value_field_is_rejected() -> None:
    entries = [_entry(size={"unit_text": "MB"})]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    with pytest.raises(SnapshotMetadataError, match="size.value"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_size_missing_unit_text_is_rejected() -> None:
    entries = [_entry(size={"value": 1.0})]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    with pytest.raises(SnapshotMetadataError, match="size.unit_text"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_empty_chunks_list_is_rejected() -> None:
    entries = [_entry(chunks=[])]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    with pytest.raises(SnapshotMetadataError, match="chunks"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_missing_chunks_field_is_rejected() -> None:
    raw_entry = _entry()
    del raw_entry["chunks"]
    client = SnapshotMetadataClient(_FixedTransport(_raw([raw_entry])))

    with pytest.raises(SnapshotMetadataError, match="chunks"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_non_array_response_is_rejected() -> None:
    client = SnapshotMetadataClient(_FixedTransport(json.dumps({"not": "a list"}).encode("utf-8")))

    with pytest.raises(SnapshotMetadataError, match="JSON array"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_empty_list_is_rejected() -> None:
    client = SnapshotMetadataClient(_FixedTransport(b"[]"))

    with pytest.raises(SnapshotMetadataError, match="zero snapshots"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_malformed_json_is_rejected() -> None:
    client = SnapshotMetadataClient(_FixedTransport(b"not json"))

    with pytest.raises(SnapshotMetadataError, match="not valid JSON"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_oversized_response_is_rejected() -> None:
    entries = [_entry()]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries) + b" " * (5 * 1024 * 1024)))

    with pytest.raises(SnapshotMetadataError, match="exceeded"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="latest")


def test_duplicate_version_identifiers_are_rejected() -> None:
    entries = [
        _entry(identifier="jawiki_namespace_0", version="2026-07-01T00:00:00Z"),
        _entry(identifier="jawiki_namespace_0_dup", version="2026-07-01T00:00:00Z"),
    ]
    client = SnapshotMetadataClient(_FixedTransport(_raw(entries)))

    with pytest.raises(SnapshotMetadataError, match="multiple Snapshots"):
        client.resolve(
            "token",
            project="jawiki",
            namespace=0,
            requested_version="2026-07-01T00:00:00Z",
        )


def test_blank_requested_version_is_rejected() -> None:
    client = SnapshotMetadataClient(_FixedTransport(_raw([_entry()])))

    with pytest.raises(SnapshotMetadataError, match="non-empty trimmed"):
        client.resolve("token", project="jawiki", namespace=0, requested_version="  ")


def test_non_positive_timeout_is_rejected() -> None:
    with pytest.raises(SnapshotMetadataError):
        SnapshotMetadataClient(_FixedTransport(b"[]"), timeout_seconds=0)


def test_client_forwards_timeout_to_transport() -> None:
    transport = _FixedTransport(_raw([_entry()]))
    client = SnapshotMetadataClient(transport, timeout_seconds=12.0)

    client.resolve("secret-token", project="jawiki", namespace=0, requested_version="latest")

    assert transport.calls == [("secret-token", 12.0)]


class _FakeResponse:
    def __init__(self, *, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self._body


def _opener_returning(status: int, entries: list[dict[str, Any]]) -> Any:
    body = _raw(entries)

    def opener(request: Any, timeout: float) -> _FakeResponse:
        assert timeout > 0
        assert request.get_header("Authorization") == "Bearer secret-token"
        return _FakeResponse(status=status, body=body)

    return opener


def test_http_transport_list_snapshots_success() -> None:
    transport = HttpSnapshotMetadataTransport(
        "https://api.enterprise.wikimedia.com/v2",
        opener=_opener_returning(200, [_entry()]),
    )

    raw = transport.list_snapshots("secret-token", timeout_seconds=5.0)

    assert json.loads(raw)[0]["identifier"] == "jawiki_namespace_0"


def test_http_transport_requires_https() -> None:
    with pytest.raises(SnapshotMetadataError):
        HttpSnapshotMetadataTransport("http://api.enterprise.wikimedia.com/v2")


def test_http_transport_requires_access_token() -> None:
    transport = HttpSnapshotMetadataTransport(
        "https://api.enterprise.wikimedia.com/v2",
        opener=_opener_returning(200, [_entry()]),
    )

    with pytest.raises(SnapshotMetadataError, match="must not be empty"):
        transport.list_snapshots("", timeout_seconds=5.0)


def test_http_transport_401_raises_immediately() -> None:
    def opener(request: Any, timeout: float) -> Any:
        raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", None, None)

    transport = HttpSnapshotMetadataTransport(
        "https://api.enterprise.wikimedia.com/v2", opener=opener
    )

    with pytest.raises(SnapshotMetadataError, match="401"):
        transport.list_snapshots("secret-token", timeout_seconds=5.0)


def test_http_transport_5xx_raises() -> None:
    def opener(request: Any, timeout: float) -> Any:
        raise urllib.error.HTTPError(request.full_url, 503, "unavailable", None, None)

    transport = HttpSnapshotMetadataTransport(
        "https://api.enterprise.wikimedia.com/v2", opener=opener
    )

    with pytest.raises(SnapshotMetadataError, match="503"):
        transport.list_snapshots("secret-token", timeout_seconds=5.0)


def test_http_transport_timeout_raises() -> None:
    def opener(request: Any, timeout: float) -> Any:
        raise TimeoutError("timed out")

    transport = HttpSnapshotMetadataTransport(
        "https://api.enterprise.wikimedia.com/v2", opener=opener
    )

    with pytest.raises(SnapshotMetadataError, match="timed out"):
        transport.list_snapshots("secret-token", timeout_seconds=1.0)


def test_http_transport_non_positive_timeout_is_rejected() -> None:
    transport = HttpSnapshotMetadataTransport(
        "https://api.enterprise.wikimedia.com/v2",
        opener=_opener_returning(200, [_entry()]),
    )

    with pytest.raises(SnapshotMetadataError):
        transport.list_snapshots("secret-token", timeout_seconds=0)
