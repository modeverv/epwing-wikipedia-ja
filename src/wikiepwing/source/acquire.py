"""Acquire orchestration: resolve metadata, download chunks, verify, write source lock."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from wikiepwing.secrets import EnterpriseSecrets
from wikiepwing.source.auth import ResolvedAccessToken
from wikiepwing.source.checksums import compute_fingerprint, verify_fingerprint
from wikiepwing.source.downloader import ChunkDownloadResult
from wikiepwing.source.enterprise import ResolvedSnapshot
from wikiepwing.source.lockfile import (
    SourceLock,
    SourceLockAcquirer,
    SourceLockFile,
    build_source_lock,
    write_source_lock,
)

PROVIDER = "wikimedia-enterprise-snapshot"
CHUNK_MEDIA_TYPE = "application/gzip"


class AcquireError(RuntimeError):
    """Raised when a Snapshot cannot be acquired safely."""


@dataclass(frozen=True, slots=True)
class AcquireResult:
    """Where an acquired Snapshot and its lock file ended up."""

    snapshot_directory: Path
    lock_path: Path
    lock: SourceLock


class AuthResolver(Protocol):
    """The subset of `EnterpriseAuthClient` this orchestration relies on."""

    def resolve(self, secrets: EnterpriseSecrets) -> ResolvedAccessToken: ...


class MetadataResolver(Protocol):
    """The subset of `SnapshotMetadataClient` this orchestration relies on."""

    def resolve(
        self,
        access_token: str,
        *,
        project: str,
        namespace: int,
        requested_version: str,
    ) -> ResolvedSnapshot: ...


class ChunkDownloader(Protocol):
    """The subset of `ResumableChunkDownloader` this orchestration relies on."""

    def download(
        self,
        access_token: str,
        *,
        snapshot_identifier: str,
        chunk_identifier: str,
        destination: Path,
    ) -> ChunkDownloadResult: ...


def acquire_snapshot(
    secrets: EnterpriseSecrets,
    *,
    auth_client: AuthResolver,
    metadata_client: MetadataResolver,
    downloader: ChunkDownloader,
    project: str,
    namespace: int,
    requested_version: str,
    sources_root: Path,
    acquirer_name: str,
    acquirer_version: str,
    acquirer_git_commit: str,
) -> AcquireResult:
    """Resolve, download, verify, and lock one Snapshot version."""
    if not sources_root.is_absolute():
        raise AcquireError(f"sources_root must be an absolute path: {sources_root}")

    resolved_token = auth_client.resolve(secrets)
    resolved_snapshot = metadata_client.resolve(
        resolved_token.value,
        project=project,
        namespace=namespace,
        requested_version=requested_version,
    )

    snapshot_directory = (
        sources_root / resolved_snapshot.project / resolved_snapshot.version_identifier
    )
    if snapshot_directory.is_symlink():
        raise AcquireError(f"snapshot directory must not be a symlink: {snapshot_directory}")
    snapshot_directory.mkdir(parents=True, exist_ok=True)

    files: list[SourceLockFile] = []
    for chunk_identifier in resolved_snapshot.chunk_identifiers:
        relative_path = f"{chunk_identifier}.tar.gz"
        destination = snapshot_directory / relative_path
        if destination.is_symlink():
            raise AcquireError(f"chunk destination must not be a symlink: {destination}")
        if destination.is_file():
            fingerprint = compute_fingerprint(destination)
        else:
            result = downloader.download(
                resolved_token.value,
                snapshot_identifier=resolved_snapshot.snapshot_identifier,
                chunk_identifier=chunk_identifier,
                destination=destination,
            )
            fingerprint = verify_fingerprint(
                destination,
                expected_size_bytes=result.size_bytes,
                expected_sha256=result.sha256,
            )
        files.append(
            SourceLockFile(
                relative_path=relative_path,
                chunk_identifier=chunk_identifier,
                size_bytes=fingerprint.size_bytes,
                sha256=fingerprint.sha256,
                media_type=CHUNK_MEDIA_TYPE,
            )
        )

    lock = build_source_lock(
        provider=PROVIDER,
        project=resolved_snapshot.project,
        namespace=resolved_snapshot.namespace,
        snapshot_identifier=resolved_snapshot.snapshot_identifier,
        snapshot_version=resolved_snapshot.version_identifier,
        date_modified=resolved_snapshot.date_modified,
        downloaded_at=datetime.now(UTC),
        files=files,
        metadata_response_sha256=resolved_snapshot.metadata_response_sha256,
        acquirer=SourceLockAcquirer(
            name=acquirer_name,
            version=acquirer_version,
            git_commit=acquirer_git_commit,
        ),
    )
    lock_path = snapshot_directory / "source.lock.json"
    write_source_lock(lock, lock_path)
    return AcquireResult(snapshot_directory=snapshot_directory, lock_path=lock_path, lock=lock)
