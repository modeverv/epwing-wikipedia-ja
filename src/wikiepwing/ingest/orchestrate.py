"""Ingest orchestration: stream chunks, parse/validate/dedupe/write, emit progress and manifest."""

from __future__ import annotations

import itertools
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from wikiepwing.ingest.database import connect_raw_database, initialize_raw_database
from wikiepwing.ingest.deduplicate import resolve_duplicate
from wikiepwing.ingest.record_parser import RecordParseError, parse_record
from wikiepwing.ingest.repository import RawRepository
from wikiepwing.ingest.tar_reader import iter_ndjson_lines
from wikiepwing.ingest.validate import ValidationLimits, validate_article
from wikiepwing.pipeline.resume import decide_resume
from wikiepwing.pipeline.stage_manifest import StageManifestError, parse_manifest_timestamp
from wikiepwing.pipeline.stage_manifest import extract_status as _extract_manifest_status
from wikiepwing.pipeline.stage_manifest import read_manifest_payload as _read_manifest_payload
from wikiepwing.pipeline.stage_manifest import (
    write_stage_manifest_payload as _write_stage_manifest_payload,
)
from wikiepwing.source.checksums import FingerprintError, compute_fingerprint, verify_fingerprint
from wikiepwing.source.lockfile import SourceLock

SCHEMA_VERSION = 1
STAGE_NAME = "30-ingest"
STAGE_VERSION = 1
DEFAULT_BATCH_SIZE = 500


class IngestError(RuntimeError):
    """Raised when an ingest run cannot complete safely."""


@dataclass(slots=True)
class IngestMetrics:
    """Running counters matching the stage manifest's `metrics` object."""

    records_read: int = 0
    records_written: int = 0
    records_rejected: int = 0
    warnings: int = 0
    errors: int = 0
    fatals: int = 0

    def payload(self) -> dict[str, object]:
        """Return this counter set as a JSON-serializable mapping."""
        return {
            "records_read": self.records_read,
            "records_written": self.records_written,
            "records_rejected": self.records_rejected,
            "warnings": self.warnings,
            "errors": self.errors,
            "fatals": self.fatals,
        }


@dataclass(frozen=True, slots=True)
class IngestManifest:
    """A stage manifest for one ingest run (DATA_CONTRACTS.md section 3)."""

    schema_version: int
    stage: str
    stage_version: int
    status: str
    run_id: str
    started_at: datetime
    completed_at: datetime | None
    inputs: dict[str, str]
    outputs: tuple[dict[str, object], ...]
    metrics: IngestMetrics
    software: dict[str, str | None]

    def payload(self) -> dict[str, object]:
        """Return this manifest as a JSON-serializable mapping."""
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "stage_version": self.stage_version,
            "status": self.status,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "inputs": self.inputs,
            "outputs": list(self.outputs),
            "metrics": self.metrics.payload(),
            "software": self.software,
        }


@dataclass(frozen=True, slots=True)
class IngestResult:
    """What one ingest run produced."""

    manifest: IngestManifest
    manifest_path: Path
    raw_database_path: Path


def read_manifest_status(manifest_path: Path) -> str | None:
    """Return a manifest's `status` field, or None if no manifest exists yet.

    Raises IngestError if the file exists but cannot be parsed as a valid manifest
    (treated the same as the "invalid" status in DATA_CONTRACTS.md's status enum).
    """
    try:
        payload = _read_manifest_payload(manifest_path)
    except StageManifestError as error:
        raise IngestError(str(error)) from error
    if payload is None:
        return None
    try:
        return _extract_manifest_status(payload, manifest_path)
    except StageManifestError as error:
        raise IngestError(str(error)) from error


def run_ingest(
    lock: SourceLock,
    *,
    snapshot_directory: Path,
    raw_database_path: Path,
    migrations_path: Path | None,
    manifest_path: Path,
    run_id: str,
    validation_limits: ValidationLimits,
    zstd_level: int = 6,
    batch_size: int = DEFAULT_BATCH_SIZE,
    git_commit: str | None = None,
    force: bool = False,
    on_progress: Callable[[IngestMetrics], None] | None = None,
) -> IngestResult:
    """Verify chunk files, then stream/parse/validate/dedupe/write each into raw.sqlite3.

    If a prior run at `manifest_path` was interrupted (its manifest is still marked
    "running"), this refuses to start a new run unless `force=True` is passed, since
    an ingest into the same raw.sqlite3 may already be in progress. Accepted/rejected
    article writes are idempotent per page_id (revision/hash based), so re-running
    after a confirmed-dead interrupted run is safe for article data; however,
    `diagnostics` and `ingest_duplicates` are append-only and are not run-scoped in
    the current schema, so a rerun may duplicate audit rows for records processed in
    both the interrupted and the rerun attempt.

    If the previous manifest at `manifest_path` shows status "complete" with a
    matching `stage_version` and matching input fingerprints, this stage is
    skipped entirely and the previous manifest is returned as-is (TASK-I005's
    `decide_resume`). Pass `force=True` to always rerun.
    """
    if batch_size < 1:
        raise IngestError("batch_size must be positive")
    previous_status = read_manifest_status(manifest_path)
    if previous_status == "running" and not force:
        raise IngestError(
            f"manifest {manifest_path} shows a previous run still 'running'; "
            "pass force=True to proceed after confirming that run is dead"
        )
    if not force:
        previous_payload = _read_manifest_payload(manifest_path)
        decision = decide_resume(
            previous_payload,
            stage_version=STAGE_VERSION,
            current_inputs=_manifest_inputs(lock),
        )
        if decision.should_skip:
            assert previous_payload is not None
            return _resume_result(previous_payload, manifest_path, raw_database_path)
    started_at = datetime.now(UTC)

    for file in lock.files:
        chunk_path = snapshot_directory / file.relative_path
        try:
            verify_fingerprint(
                chunk_path, expected_size_bytes=file.size_bytes, expected_sha256=file.sha256
            )
        except FingerprintError as error:
            raise IngestError(
                f"chunk verification failed for {file.relative_path}: {error}"
            ) from error

    metrics = IngestMetrics()
    _write_manifest(
        _build_manifest(
            status="running",
            run_id=run_id,
            started_at=started_at,
            completed_at=None,
            lock=lock,
            database_path=None,
            metrics=metrics,
            git_commit=git_commit,
        ),
        manifest_path,
    )

    database_path = initialize_raw_database(raw_database_path, migrations_path)
    status = "failed"
    try:
        connection = connect_raw_database(database_path)
        try:
            repository = RawRepository(connection, zstd_level=zstd_level)
            for file in lock.files:
                chunk_path = snapshot_directory / file.relative_path
                _ingest_chunk(
                    chunk_path,
                    repository=repository,
                    metrics=metrics,
                    validation_limits=validation_limits,
                    batch_size=batch_size,
                    on_progress=on_progress,
                )
            status = "complete"
        finally:
            connection.close()
    finally:
        manifest = _build_manifest(
            status=status,
            run_id=run_id,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            lock=lock,
            database_path=database_path,
            metrics=metrics,
            git_commit=git_commit,
        )
        _write_manifest(manifest, manifest_path)

    return IngestResult(
        manifest=manifest, manifest_path=manifest_path, raw_database_path=database_path
    )


def _manifest_inputs(lock: SourceLock) -> dict[str, str]:
    return {"source_lock": f"sha256:{lock.metadata_response_sha256}"}


def _resume_result(
    previous_payload: dict[str, object], manifest_path: Path, raw_database_path: Path
) -> IngestResult:
    metrics = IngestMetrics(**cast(dict[str, int], previous_payload["metrics"]))
    manifest = IngestManifest(
        schema_version=cast(int, previous_payload["schema_version"]),
        stage=STAGE_NAME,
        stage_version=cast(int, previous_payload["stage_version"]),
        status=cast(str, previous_payload["status"]),
        run_id=cast(str, previous_payload["run_id"]),
        started_at=cast(datetime, parse_manifest_timestamp(previous_payload["started_at"])),
        completed_at=parse_manifest_timestamp(previous_payload["completed_at"]),
        inputs=cast(dict[str, str], previous_payload["inputs"]),
        outputs=tuple(cast(list[dict[str, object]], previous_payload["outputs"])),
        metrics=metrics,
        software=cast(dict[str, str | None], previous_payload["software"]),
    )
    return IngestResult(
        manifest=manifest, manifest_path=manifest_path, raw_database_path=raw_database_path
    )


def _build_manifest(
    *,
    status: str,
    run_id: str,
    started_at: datetime,
    completed_at: datetime | None,
    lock: SourceLock,
    database_path: Path | None,
    metrics: IngestMetrics,
    git_commit: str | None,
) -> IngestManifest:
    outputs: tuple[dict[str, object], ...] = ()
    if database_path is not None and database_path.is_file():
        fingerprint = compute_fingerprint(database_path)
        outputs = (
            {
                "relative_path": database_path.name,
                "size_bytes": fingerprint.size_bytes,
                "sha256": fingerprint.sha256,
                "logical_hash": None,
            },
        )
    return IngestManifest(
        schema_version=SCHEMA_VERSION,
        stage=STAGE_NAME,
        stage_version=STAGE_VERSION,
        status=status,
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        inputs=_manifest_inputs(lock),
        outputs=outputs,
        metrics=metrics,
        software={
            "git_commit": git_commit,
            "app_image_digest": None,
            "toolchain_image_digest": None,
        },
    )


def _ingest_chunk(
    chunk_path: Path,
    *,
    repository: RawRepository,
    metrics: IngestMetrics,
    validation_limits: ValidationLimits,
    batch_size: int,
    on_progress: Callable[[IngestMetrics], None] | None,
) -> None:
    numbered_lines: Iterator[tuple[int, bytes]] = enumerate(iter_ndjson_lines(chunk_path))
    while True:
        group = list(itertools.islice(numbered_lines, batch_size))
        if not group:
            return
        with repository.batch():
            for sequence, line in group:
                _process_one_record(
                    line,
                    sequence,
                    repository=repository,
                    metrics=metrics,
                    validation_limits=validation_limits,
                )
        if on_progress is not None:
            on_progress(metrics)


def _process_one_record(
    line: bytes,
    sequence: int,
    *,
    repository: RawRepository,
    metrics: IngestMetrics,
    validation_limits: ValidationLimits,
) -> None:
    metrics.records_read += 1
    try:
        article = parse_record(line, source_sequence=sequence)
    except RecordParseError:
        metrics.errors += 1
        return

    existing = repository.get_existing_accepted(article.page_id)
    resolution = resolve_duplicate(existing, article)
    if resolution.duplicate_record is not None:
        repository.write_duplicate(resolution.duplicate_record)
    if resolution.diagnostic is not None:
        repository.write_diagnostic(
            resolution.diagnostic, stage=STAGE_NAME, page_id=article.page_id, title=article.title
        )
        metrics.errors += 1
    if not resolution.keep_new:
        return

    result = validate_article(article, validation_limits)
    for diagnostic in result.diagnostics:
        repository.write_diagnostic(
            diagnostic, stage=STAGE_NAME, page_id=article.page_id, title=article.title
        )
        if diagnostic.severity == "warning":
            metrics.warnings += 1
        elif diagnostic.severity in ("error", "fatal"):
            metrics.errors += 1

    if result.accepted:
        repository.write_accepted_article(article)
        metrics.records_written += 1
    else:
        repository.write_rejected_article(article)
        metrics.records_rejected += 1


def _write_manifest(manifest: IngestManifest, destination: Path) -> None:
    _write_stage_manifest_payload(manifest.payload(), destination)
