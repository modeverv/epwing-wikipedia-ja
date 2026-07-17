from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from wikiepwing.secrets import EnterpriseSecrets
from wikiepwing.source.acquire import (
    AcquireChunkProgress,
    AcquireError,
    AcquireProgress,
    acquire_snapshot,
)
from wikiepwing.source.auth import ResolvedAccessToken
from wikiepwing.source.checksums import FingerprintError
from wikiepwing.source.downloader import ChunkDownloadProgress, ChunkDownloadResult
from wikiepwing.source.enterprise import ResolvedSnapshot

SECRETS = EnterpriseSecrets(
    username=None, password=None, access_token="fixed-token", refresh_token=None
)


def _resolved_snapshot(**overrides: object) -> ResolvedSnapshot:
    defaults: dict[str, object] = {
        "project": "jawiki",
        "namespace": 0,
        "snapshot_identifier": "jawiki_namespace_0",
        "version_identifier": "35061ecbd3bc55c31cffd4b46838673d",
        "date_modified": datetime(2026, 7, 1, 0, 50, 43, tzinfo=UTC),
        "size_bytes": None,
        "metadata_response_sha256": "b" * 64,
    }
    defaults.update(overrides)
    chunk_identifiers = overrides.get("chunk_identifiers", ("jawiki_namespace_0_chunk_0",))
    return ResolvedSnapshot(
        project=defaults["project"],  # type: ignore[arg-type]
        namespace=defaults["namespace"],  # type: ignore[arg-type]
        snapshot_identifier=defaults["snapshot_identifier"],  # type: ignore[arg-type]
        version_identifier=defaults["version_identifier"],  # type: ignore[arg-type]
        date_modified=defaults["date_modified"],  # type: ignore[arg-type]
        size_estimate=None,
        chunk_identifiers=chunk_identifiers,  # type: ignore[arg-type]
        metadata_response_sha256=defaults["metadata_response_sha256"],  # type: ignore[arg-type]
    )


class _FakeAuthClient:
    def __init__(self, token: str = "resolved-token") -> None:
        self._token = token
        self.resolve_calls = 0

    def resolve(self, secrets: EnterpriseSecrets) -> ResolvedAccessToken:
        self.resolve_calls += 1
        return ResolvedAccessToken(self._token, "access_token")


class _FakeMetadataClient:
    def __init__(self, resolved: ResolvedSnapshot) -> None:
        self._resolved = resolved
        self.calls: list[tuple[str, str, int, str]] = []

    def resolve(
        self, access_token: str, *, project: str, namespace: int, requested_version: str
    ) -> ResolvedSnapshot:
        self.calls.append((access_token, project, namespace, requested_version))
        return self._resolved


class _FakeDownloader:
    def __init__(
        self, contents: dict[str, bytes], *, lie_about: dict[str, bytes] | None = None
    ) -> None:
        self._contents = contents
        self._lie_about = lie_about or {}
        self.calls: list[dict[str, Any]] = []

    def download(
        self,
        access_token: str,
        *,
        snapshot_identifier: str,
        chunk_identifier: str,
        destination: Path,
        on_progress: Callable[[ChunkDownloadProgress], None] | None = None,
    ) -> ChunkDownloadResult:
        self.calls.append(
            {
                "access_token": access_token,
                "snapshot_identifier": snapshot_identifier,
                "chunk_identifier": chunk_identifier,
                "destination": destination,
            }
        )
        data = self._contents[chunk_identifier]
        if on_progress is not None:
            on_progress(ChunkDownloadProgress(bytes_downloaded=len(data), total_bytes=len(data)))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        reported = self._lie_about.get(chunk_identifier, data)
        return ChunkDownloadResult(
            size_bytes=len(reported), sha256=hashlib.sha256(reported).hexdigest()
        )


def test_acquires_single_chunk_and_writes_lock(tmp_path: Path) -> None:
    resolved = _resolved_snapshot(chunk_identifiers=("jawiki_namespace_0_chunk_0",))
    auth_client = _FakeAuthClient("resolved-token")
    metadata_client = _FakeMetadataClient(resolved)
    content = b"tar-gz-bytes"
    downloader = _FakeDownloader({"jawiki_namespace_0_chunk_0": content})

    result = acquire_snapshot(
        SECRETS,
        auth_client=auth_client,
        metadata_client=metadata_client,
        downloader=downloader,
        project="jawiki",
        namespace=0,
        requested_version="latest",
        sources_root=tmp_path,
        acquirer_name="wikiepwing",
        acquirer_version="0.1.0",
        acquirer_git_commit="abc1234",
    )

    assert result.snapshot_directory == tmp_path / "jawiki" / resolved.version_identifier
    assert result.lock_path == result.snapshot_directory / "source.lock.json"
    assert result.lock_path.is_file()
    assert (result.snapshot_directory / "jawiki_namespace_0_chunk_0.tar.gz").read_bytes() == content

    on_disk = json.loads(result.lock_path.read_bytes())
    assert on_disk == result.lock.payload()
    assert on_disk["provider"] == "wikimedia-enterprise-snapshot"
    assert on_disk["project"] == "jawiki"
    assert on_disk["namespace"] == 0
    assert on_disk["snapshot_version"] == resolved.version_identifier
    assert on_disk["metadata_response_sha256"] == "b" * 64
    assert len(on_disk["files"]) == 1
    assert on_disk["files"][0]["relative_path"] == "jawiki_namespace_0_chunk_0.tar.gz"
    assert on_disk["files"][0]["sha256"] == hashlib.sha256(content).hexdigest()
    assert on_disk["acquirer"] == {
        "name": "wikiepwing",
        "version": "0.1.0",
        "git_commit": "abc1234",
    }
    assert auth_client.resolve_calls == 1
    assert metadata_client.calls == [("resolved-token", "jawiki", 0, "latest")]


def test_acquires_multiple_chunks_in_order(tmp_path: Path) -> None:
    resolved = _resolved_snapshot(chunk_identifiers=("chunk_0", "chunk_1", "chunk_2"))
    downloader = _FakeDownloader({"chunk_0": b"AAA", "chunk_1": b"BBB", "chunk_2": b"CCC"})

    result = acquire_snapshot(
        SECRETS,
        auth_client=_FakeAuthClient(),
        metadata_client=_FakeMetadataClient(resolved),
        downloader=downloader,
        project="jawiki",
        namespace=0,
        requested_version="latest",
        sources_root=tmp_path,
        acquirer_name="wikiepwing",
        acquirer_version="0.1.0",
        acquirer_git_commit="abc1234",
    )

    identifiers = [file.chunk_identifier for file in result.lock.files]
    assert identifiers == ["chunk_0", "chunk_1", "chunk_2"]
    assert len(downloader.calls) == 3


def test_on_progress_reports_one_event_per_chunk_in_order(tmp_path: Path) -> None:
    resolved = _resolved_snapshot(chunk_identifiers=("chunk_0", "chunk_1", "chunk_2"))
    downloader = _FakeDownloader({"chunk_0": b"AAA", "chunk_1": b"BB", "chunk_2": b"C"})
    events: list[AcquireProgress] = []

    acquire_snapshot(
        SECRETS,
        auth_client=_FakeAuthClient(),
        metadata_client=_FakeMetadataClient(resolved),
        downloader=downloader,
        project="jawiki",
        namespace=0,
        requested_version="latest",
        sources_root=tmp_path,
        acquirer_name="wikiepwing",
        acquirer_version="0.1.0",
        acquirer_git_commit="abc1234",
        on_progress=events.append,
    )

    assert [(event.chunks_completed, event.chunk_identifier) for event in events] == [
        (1, "chunk_0"),
        (2, "chunk_1"),
        (3, "chunk_2"),
    ]
    assert [event.chunks_total for event in events] == [3, 3, 3]
    assert [event.size_bytes for event in events] == [3, 2, 1]
    assert [event.already_present for event in events] == [False, False, False]


def test_on_progress_marks_already_present_chunks(tmp_path: Path) -> None:
    resolved = _resolved_snapshot(chunk_identifiers=("chunk_0",))
    snapshot_dir = tmp_path / "jawiki" / resolved.version_identifier
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "chunk_0.tar.gz").write_bytes(b"already-here")
    events: list[AcquireProgress] = []

    acquire_snapshot(
        SECRETS,
        auth_client=_FakeAuthClient(),
        metadata_client=_FakeMetadataClient(resolved),
        downloader=_FakeDownloader({"chunk_0": b"would-be-fresh-download"}),
        project="jawiki",
        namespace=0,
        requested_version="latest",
        sources_root=tmp_path,
        acquirer_name="wikiepwing",
        acquirer_version="0.1.0",
        acquirer_git_commit="abc1234",
        on_progress=events.append,
    )

    assert len(events) == 1
    assert events[0].already_present is True


def test_on_chunk_progress_reports_bytes_downloaded_mid_chunk(tmp_path: Path) -> None:
    resolved = _resolved_snapshot(chunk_identifiers=("chunk_0",))
    downloader = _FakeDownloader({"chunk_0": b"hello world"})
    events: list[AcquireChunkProgress] = []

    acquire_snapshot(
        SECRETS,
        auth_client=_FakeAuthClient(),
        metadata_client=_FakeMetadataClient(resolved),
        downloader=downloader,
        project="jawiki",
        namespace=0,
        requested_version="latest",
        sources_root=tmp_path,
        acquirer_name="wikiepwing",
        acquirer_version="0.1.0",
        acquirer_git_commit="abc1234",
        on_chunk_progress=events.append,
    )

    assert len(events) == 1
    assert events[0].chunk_identifier == "chunk_0"
    assert events[0].chunk_index == 1
    assert events[0].chunks_total == 1
    assert events[0].bytes_downloaded == len(b"hello world")
    assert events[0].total_bytes == len(b"hello world")


def test_skips_redownload_when_chunk_already_present(tmp_path: Path) -> None:
    resolved = _resolved_snapshot(chunk_identifiers=("chunk_0",))
    snapshot_dir = tmp_path / "jawiki" / resolved.version_identifier
    snapshot_dir.mkdir(parents=True)
    existing_content = b"already-downloaded"
    (snapshot_dir / "chunk_0.tar.gz").write_bytes(existing_content)
    downloader = _FakeDownloader({"chunk_0": b"would-be-fresh-download"})

    result = acquire_snapshot(
        SECRETS,
        auth_client=_FakeAuthClient(),
        metadata_client=_FakeMetadataClient(resolved),
        downloader=downloader,
        project="jawiki",
        namespace=0,
        requested_version="latest",
        sources_root=tmp_path,
        acquirer_name="wikiepwing",
        acquirer_version="0.1.0",
        acquirer_git_commit="abc1234",
    )

    assert downloader.calls == []
    assert result.lock.files[0].sha256 == hashlib.sha256(existing_content).hexdigest()
    assert (snapshot_dir / "chunk_0.tar.gz").read_bytes() == existing_content


def test_corrupted_download_result_is_rejected(tmp_path: Path) -> None:
    resolved = _resolved_snapshot(chunk_identifiers=("chunk_0",))
    downloader = _FakeDownloader(
        {"chunk_0": b"real-bytes-on-disk"},
        lie_about={"chunk_0": b"a-completely-different-value"},
    )

    with pytest.raises(FingerprintError, match="mismatch"):
        acquire_snapshot(
            SECRETS,
            auth_client=_FakeAuthClient(),
            metadata_client=_FakeMetadataClient(resolved),
            downloader=downloader,
            project="jawiki",
            namespace=0,
            requested_version="latest",
            sources_root=tmp_path,
            acquirer_name="wikiepwing",
            acquirer_version="0.1.0",
            acquirer_git_commit="abc1234",
        )


def test_sources_root_must_be_absolute() -> None:
    resolved = _resolved_snapshot()

    with pytest.raises(AcquireError, match="absolute"):
        acquire_snapshot(
            SECRETS,
            auth_client=_FakeAuthClient(),
            metadata_client=_FakeMetadataClient(resolved),
            downloader=_FakeDownloader({}),
            project="jawiki",
            namespace=0,
            requested_version="latest",
            sources_root=Path("relative/sources"),
            acquirer_name="wikiepwing",
            acquirer_version="0.1.0",
            acquirer_git_commit="abc1234",
        )


def test_snapshot_directory_symlink_is_rejected(tmp_path: Path) -> None:
    resolved = _resolved_snapshot()
    (tmp_path / "jawiki").mkdir()
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (tmp_path / "jawiki" / resolved.version_identifier).symlink_to(real_dir)

    with pytest.raises(AcquireError, match="symlink"):
        acquire_snapshot(
            SECRETS,
            auth_client=_FakeAuthClient(),
            metadata_client=_FakeMetadataClient(resolved),
            downloader=_FakeDownloader({}),
            project="jawiki",
            namespace=0,
            requested_version="latest",
            sources_root=tmp_path,
            acquirer_name="wikiepwing",
            acquirer_version="0.1.0",
            acquirer_git_commit="abc1234",
        )


def test_chunk_destination_symlink_is_rejected(tmp_path: Path) -> None:
    resolved = _resolved_snapshot(chunk_identifiers=("chunk_0",))
    snapshot_dir = tmp_path / "jawiki" / resolved.version_identifier
    snapshot_dir.mkdir(parents=True)
    real_file = tmp_path / "elsewhere.tar.gz"
    real_file.write_bytes(b"x")
    (snapshot_dir / "chunk_0.tar.gz").symlink_to(real_file)

    with pytest.raises(AcquireError, match="symlink"):
        acquire_snapshot(
            SECRETS,
            auth_client=_FakeAuthClient(),
            metadata_client=_FakeMetadataClient(resolved),
            downloader=_FakeDownloader({"chunk_0": b"y"}),
            project="jawiki",
            namespace=0,
            requested_version="latest",
            sources_root=tmp_path,
            acquirer_name="wikiepwing",
            acquirer_version="0.1.0",
            acquirer_git_commit="abc1234",
        )
