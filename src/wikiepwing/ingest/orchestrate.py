"""Ingest orchestration: stream chunks, parse/validate/dedupe/write, emit progress and manifest."""

from __future__ import annotations

import itertools
import json
import os
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from wikiepwing.ingest.database import connect_raw_database, initialize_raw_database
from wikiepwing.ingest.deduplicate import resolve_duplicate
from wikiepwing.ingest.record_parser import RecordParseError, parse_record
from wikiepwing.ingest.repository import RawRepository
from wikiepwing.ingest.tar_reader import iter_ndjson_lines
from wikiepwing.ingest.validate import ValidationLimits, validate_article
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
    on_progress: Callable[[IngestMetrics], None] | None = None,
) -> IngestResult:
    """Verify chunk files, then stream/parse/validate/dedupe/write each into raw.sqlite3."""
    if batch_size < 1:
        raise IngestError("batch_size must be positive")
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

    database_path = initialize_raw_database(raw_database_path, migrations_path)
    metrics = IngestMetrics()
    status = "failed"
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

    completed_at = datetime.now(UTC)
    fingerprint = compute_fingerprint(database_path)
    manifest = IngestManifest(
        schema_version=SCHEMA_VERSION,
        stage=STAGE_NAME,
        stage_version=STAGE_VERSION,
        status=status,
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        inputs={"metadata_response_sha256": lock.metadata_response_sha256},
        outputs=(
            {
                "relative_path": database_path.name,
                "size_bytes": fingerprint.size_bytes,
                "sha256": fingerprint.sha256,
                "logical_hash": None,
            },
        ),
        metrics=metrics,
        software={
            "git_commit": git_commit,
            "app_image_digest": None,
            "toolchain_image_digest": None,
        },
    )
    _write_manifest(manifest, manifest_path)
    return IngestResult(
        manifest=manifest, manifest_path=manifest_path, raw_database_path=database_path
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
    payload = json.dumps(manifest.payload(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", delete=False
    )
    try:
        temp_path = Path(handle.name)
        handle.write(payload.encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    os.replace(temp_path, destination)
