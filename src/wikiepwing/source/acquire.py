"""Acquire orchestration: resolve metadata, download chunks, verify, write source lock."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from wikiepwing.secrets import EnterpriseSecrets
from wikiepwing.source.auth import ResolvedAccessToken
from wikiepwing.source.checksums import compute_fingerprint, verify_fingerprint
from wikiepwing.source.downloader import ChunkDownloadProgress, ChunkDownloadResult
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


@dataclass(frozen=True, slots=True)
class AcquireProgress:
    """One chunk's completion, reported after it is downloaded or found already present."""

    chunks_completed: int
    chunks_total: int
    chunk_identifier: str
    size_bytes: int
    already_present: bool


@dataclass(frozen=True, slots=True)
class AcquireChunkProgress:
    """In-progress byte count for the chunk currently downloading."""

    chunk_index: int
    chunks_total: int
    chunk_identifier: str
    bytes_downloaded: int
    total_bytes: int


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
        on_progress: Callable[[ChunkDownloadProgress], None] | None = None,
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
    on_progress: Callable[[AcquireProgress], None] | None = None,
    on_chunk_progress: Callable[[AcquireChunkProgress], None] | None = None,
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
    chunks_total = len(resolved_snapshot.chunk_identifiers)
    for chunks_completed, chunk_identifier in enumerate(
        resolved_snapshot.chunk_identifiers, start=1
    ):
        relative_path = f"{chunk_identifier}.tar.gz"
        destination = snapshot_directory / relative_path
        if destination.is_symlink():
            raise AcquireError(f"chunk destination must not be a symlink: {destination}")
        already_present = destination.is_file()
        if already_present:
            fingerprint = compute_fingerprint(destination)
        else:
            chunk_progress_callback = None
            if on_chunk_progress is not None:

                def chunk_progress_callback(
                    progress: ChunkDownloadProgress,
                    _index: int = chunks_completed,
                    _identifier: str = chunk_identifier,
                ) -> None:
                    on_chunk_progress(
                        AcquireChunkProgress(
                            chunk_index=_index,
                            chunks_total=chunks_total,
                            chunk_identifier=_identifier,
                            bytes_downloaded=progress.bytes_downloaded,
                            total_bytes=progress.total_bytes,
                        )
                    )

            result = downloader.download(
                resolved_token.value,
                snapshot_identifier=resolved_snapshot.snapshot_identifier,
                chunk_identifier=chunk_identifier,
                destination=destination,
                on_progress=chunk_progress_callback,
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
        if on_progress is not None:
            on_progress(
                AcquireProgress(
                    chunks_completed=chunks_completed,
                    chunks_total=chunks_total,
                    chunk_identifier=chunk_identifier,
                    size_bytes=fingerprint.size_bytes,
                    already_present=already_present,
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
