"""Normalize orchestration: read accepted raw articles, normalize, validate, write model.sqlite3.

Mirrors `wikiepwing.ingest.orchestrate`'s manifest lifecycle (running/complete/
failed, `--force`) for the normalize stage (TASK-G012).

`workers > 1` parallelizes the one genuinely CPU-bound, per-article, side-
effect-free step (`normalize_html` through hashing) across a process pool
(TASK-T009; `[normalize].workers`/`queue_depth` were declared in config
since early in the project but never wired to anything -- this is the
first code that reads `workers`). Every other per-article step --
`raw.sqlite3` reads (redirects/categories/media/licenses) and the
`model.sqlite3` write -- stays on the main process, sequential, in
`page_id` order, exactly as before: batches are still read via
`fetchmany`/written via one `repository.batch()` each, so this does not
change memory use, output ordering, or (per
`test_normalize_parallel_matches_sequential_output`) the resulting
`model.sqlite3` bytes -- only how the CPU-heavy part is scheduled.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterator
from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from wikiepwing.ingest.database import connect_raw_database
from wikiepwing.ingest.zstd_codec import decompress
from wikiepwing.links.redirect_aliases import extract_redirect_aliases
from wikiepwing.model.article import Alias, Article, MediaReference
from wikiepwing.model.blocks import (
    Block,
    InfoboxBlock,
    OrderedListBlock,
    ParagraphBlock,
    QuoteBlock,
    TableBlock,
    UnorderedListBlock,
    UnsupportedBlock,
)
from wikiepwing.model.canonical import encode_article
from wikiepwing.model.database import connect_model_database, initialize_model_database
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.logical_hash import compute_logical_hash
from wikiepwing.model.repository import ModelRepository
from wikiepwing.model.validate import ModelValidationLimits, validate_article
from wikiepwing.normalize.media_selection import select_media
from wikiepwing.normalize.pipeline import NormalizeOptions, normalize_html
from wikiepwing.pipeline.fingerprint import compute_input_fingerprint
from wikiepwing.pipeline.progress import PhaseProgress, fingerprint_progress_callback
from wikiepwing.pipeline.resume import decide_resume
from wikiepwing.pipeline.stage_manifest import StageManifestError, parse_manifest_timestamp
from wikiepwing.pipeline.stage_manifest import extract_status as _extract_manifest_status
from wikiepwing.pipeline.stage_manifest import read_manifest_payload as _read_manifest_payload
from wikiepwing.pipeline.stage_manifest import (
    write_stage_manifest_payload as _write_stage_manifest_payload,
)
from wikiepwing.source.checksums import compute_fingerprint

SCHEMA_VERSION = 1
STAGE_NAME = "40-normalize"
STAGE_VERSION = 1
DEFAULT_BATCH_SIZE = 500


class NormalizeError(RuntimeError):
    """Raised when a normalize run cannot complete safely."""


@dataclass(slots=True)
class NormalizeMetrics:
    """Running counters matching the stage manifest's `metrics` object."""

    articles_read: int = 0
    articles_written: int = 0
    articles_rejected: int = 0
    warnings: int = 0
    errors: int = 0
    fatals: int = 0

    def payload(self) -> dict[str, object]:
        """Return this counter set as a JSON-serializable mapping."""
        return {
            "articles_read": self.articles_read,
            "articles_written": self.articles_written,
            "articles_rejected": self.articles_rejected,
            "warnings": self.warnings,
            "errors": self.errors,
            "fatals": self.fatals,
        }


@dataclass(frozen=True, slots=True)
class NormalizeManifest:
    """A stage manifest for one normalize run (DATA_CONTRACTS.md section 3)."""

    schema_version: int
    stage: str
    stage_version: int
    status: str
    run_id: str
    started_at: datetime
    completed_at: datetime | None
    inputs: dict[str, str]
    outputs: tuple[dict[str, object], ...]
    metrics: NormalizeMetrics
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
class NormalizeResult:
    """What one normalize run produced."""

    manifest: NormalizeManifest
    manifest_path: Path
    model_database_path: Path


def read_manifest_status(manifest_path: Path) -> str | None:
    """Return a manifest's `status` field, or None if no manifest exists yet."""
    try:
        payload = _read_manifest_payload(manifest_path)
    except StageManifestError as error:
        raise NormalizeError(str(error)) from error
    if payload is None:
        return None
    try:
        return _extract_manifest_status(payload, manifest_path)
    except StageManifestError as error:
        raise NormalizeError(str(error)) from error


def run_normalize(
    *,
    raw_database_path: Path,
    model_database_path: Path,
    model_migrations_path: Path | None,
    manifest_path: Path,
    run_id: str,
    model_validation_limits: ModelValidationLimits,
    normalize_options: NormalizeOptions,
    zstd_level: int = 6,
    batch_size: int = DEFAULT_BATCH_SIZE,
    workers: int = 1,
    git_commit: str | None = None,
    force: bool = False,
    on_progress: Callable[[NormalizeMetrics], None] | None = None,
    on_phase_progress: Callable[[PhaseProgress], None] | None = None,
) -> NormalizeResult:
    """Normalize every accepted raw article into model.sqlite3.

    If the previous manifest at `manifest_path` shows status "complete" with
    a matching `stage_version` and matching input fingerprints, this stage is
    skipped entirely and the previous manifest is returned as-is (TASK-I005's
    `decide_resume`). Pass `force=True` to always rerun.

    `workers` (default 1, sequential -- no process pool spawned) parallelizes
    each batch's CPU-bound normalize/validate/hash step across a process
    pool without changing per-article logic, batch size, write ordering, or
    output bytes; see the module docstring.
    """
    if batch_size < 1:
        raise NormalizeError("batch_size must be positive")
    if workers < 1:
        raise NormalizeError("workers must be positive")
    previous_status = read_manifest_status(manifest_path)
    if previous_status == "running" and not force:
        raise NormalizeError(
            f"manifest {manifest_path} shows a previous run still 'running'; "
            "pass force=True to proceed after confirming that run is dead"
        )
    if not force:
        previous_payload = _read_manifest_payload(manifest_path)
        decision = decide_resume(
            previous_payload,
            stage_version=STAGE_VERSION,
            current_inputs=_manifest_inputs(raw_database_path, on_phase_progress=on_phase_progress),
            current_output_fingerprint=_current_output_fingerprint(
                model_database_path, on_phase_progress=on_phase_progress
            ),
        )
        if decision.should_skip:
            assert previous_payload is not None
            return _resume_result(previous_payload, manifest_path, model_database_path)
    started_at = datetime.now(UTC)

    metrics = NormalizeMetrics()
    _write_manifest(
        _build_manifest(
            status="running",
            run_id=run_id,
            started_at=started_at,
            completed_at=None,
            raw_database_path=raw_database_path,
            model_database_path=None,
            metrics=metrics,
            git_commit=git_commit,
            on_phase_progress=on_phase_progress,
        ),
        manifest_path,
    )

    try:
        database_path = initialize_model_database(
            model_database_path,
            model_migrations_path,
            on_integrity_progress=_integrity_progress_callback(on_phase_progress),
        )
    except sqlite3.DatabaseError:
        # The previous output was corrupted (e.g. truncated by a mid-write crash)
        # rather than a valid database we can migrate in place; discard it and
        # rebuild from scratch instead of failing this run outright.
        model_database_path.unlink(missing_ok=True)
        database_path = initialize_model_database(
            model_database_path,
            model_migrations_path,
            on_integrity_progress=_integrity_progress_callback(on_phase_progress),
        )
    status = "failed"
    try:
        raw_connection = connect_raw_database(raw_database_path)
        try:
            model_connection = connect_model_database(database_path)
            try:
                repository = ModelRepository(model_connection, zstd_level=zstd_level)
                _normalize_all(
                    raw_connection,
                    repository=repository,
                    metrics=metrics,
                    model_validation_limits=model_validation_limits,
                    normalize_options=normalize_options,
                    batch_size=batch_size,
                    workers=workers,
                    on_progress=on_progress,
                )
                status = "complete"
            finally:
                model_connection.close()
        finally:
            raw_connection.close()
    finally:
        manifest = _build_manifest(
            status=status,
            run_id=run_id,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            raw_database_path=raw_database_path,
            model_database_path=database_path,
            metrics=metrics,
            git_commit=git_commit,
            on_phase_progress=on_phase_progress,
        )
        _write_manifest(manifest, manifest_path)

    return NormalizeResult(
        manifest=manifest, manifest_path=manifest_path, model_database_path=database_path
    )


def _integrity_progress_callback(
    callback: Callable[[PhaseProgress], None] | None,
) -> Callable[[int, bool], None] | None:
    if callback is None:
        return None

    def report(completed: int, complete: bool) -> None:
        callback(
            PhaseProgress(
                phase="normalize-model-integrity",
                completed=completed,
                total=None,
                unit="vm-steps",
                complete=complete,
            )
        )

    return report


def _current_output_fingerprint(
    path: Path, *, on_phase_progress: Callable[[PhaseProgress], None] | None
) -> tuple[int, str] | None:
    if not path.is_file():
        return None
    fingerprint = compute_fingerprint(
        path,
        on_progress=fingerprint_progress_callback(
            on_phase_progress, "normalize-resume-output-fingerprint"
        ),
    )
    return (fingerprint.size_bytes, fingerprint.sha256)


def _resume_result(
    previous_payload: dict[str, object], manifest_path: Path, model_database_path: Path
) -> NormalizeResult:
    metrics = NormalizeMetrics(**cast(dict[str, int], previous_payload["metrics"]))
    manifest = NormalizeManifest(
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
    return NormalizeResult(
        manifest=manifest, manifest_path=manifest_path, model_database_path=model_database_path
    )


def _manifest_inputs(
    raw_database_path: Path,
    *,
    on_phase_progress: Callable[[PhaseProgress], None] | None = None,
) -> dict[str, str]:
    inputs = {"raw_database_path": str(raw_database_path)}
    if raw_database_path.is_file():
        inputs["raw_database_fingerprint"] = compute_input_fingerprint(
            raw_database_path,
            on_progress=fingerprint_progress_callback(
                on_phase_progress, "normalize-input-fingerprint"
            ),
        )
    return inputs


def _build_manifest(
    *,
    status: str,
    run_id: str,
    started_at: datetime,
    completed_at: datetime | None,
    raw_database_path: Path,
    model_database_path: Path | None,
    metrics: NormalizeMetrics,
    git_commit: str | None,
    on_phase_progress: Callable[[PhaseProgress], None] | None = None,
) -> NormalizeManifest:
    outputs: tuple[dict[str, object], ...] = ()
    if model_database_path is not None and model_database_path.is_file():
        fingerprint = compute_fingerprint(
            model_database_path,
            on_progress=fingerprint_progress_callback(
                on_phase_progress, "normalize-output-fingerprint"
            ),
        )
        outputs = (
            {
                "relative_path": model_database_path.name,
                "size_bytes": fingerprint.size_bytes,
                "sha256": fingerprint.sha256,
                "logical_hash": None,
            },
        )
    return NormalizeManifest(
        schema_version=SCHEMA_VERSION,
        stage=STAGE_NAME,
        stage_version=STAGE_VERSION,
        status=status,
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        inputs=_manifest_inputs(raw_database_path, on_phase_progress=on_phase_progress),
        outputs=outputs,
        metrics=metrics,
        software={
            "git_commit": git_commit,
            "app_image_digest": None,
            "toolchain_image_digest": None,
        },
    )


@dataclass(frozen=True)
class _WorkItem:
    """Everything `_compute_normalized` needs, pre-read from raw.sqlite3 so the
    function itself has no database handle and is safe to pickle/run in a
    worker process."""

    page_id: int
    revision_id: int
    title: str
    normalized_title: str
    url: str
    date_modified: str
    html_zstd: bytes | None
    aliases: tuple[Alias, ...]
    categories: tuple[str, ...]
    media: tuple[MediaReference, ...]
    license_ids: tuple[str, ...]
    model_validation_limits: ModelValidationLimits
    normalize_options: NormalizeOptions


@dataclass(frozen=True)
class _ComputedResult:
    article: Article
    canonical_json: bytes
    logical_hash: str
    normalize_status: str


def _normalize_all(
    raw_connection: sqlite3.Connection,
    *,
    repository: ModelRepository,
    metrics: NormalizeMetrics,
    model_validation_limits: ModelValidationLimits,
    normalize_options: NormalizeOptions,
    batch_size: int,
    workers: int,
    on_progress: Callable[[NormalizeMetrics], None] | None,
) -> None:
    cursor = raw_connection.execute(
        "SELECT page_id, revision_id, title, normalized_title, url, date_modified, html_zstd "
        "FROM articles WHERE ingest_status = 'accepted' AND is_deleted = 0 ORDER BY page_id"
    )
    executor_context = ProcessPoolExecutor(max_workers=workers) if workers > 1 else nullcontext()
    with executor_context as executor:
        mapper: Callable[..., Iterator[_ComputedResult]] = executor.map if executor else map
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                return
            work_items = [
                _build_work_item(
                    row,
                    raw_connection=raw_connection,
                    model_validation_limits=model_validation_limits,
                    normalize_options=normalize_options,
                )
                for row in rows
            ]
            with repository.batch():
                for result in mapper(_compute_normalized, work_items):
                    metrics.articles_read += 1
                    for diagnostic in result.article.diagnostics:
                        if diagnostic.severity == "warning":
                            metrics.warnings += 1
                        elif diagnostic.severity == "error":
                            metrics.errors += 1
                        elif diagnostic.severity == "fatal":
                            metrics.fatals += 1
                    if result.normalize_status == "rejected":
                        metrics.articles_rejected += 1
                    else:
                        metrics.articles_written += 1
                    repository.write_article(
                        result.article,
                        canonical_json=result.canonical_json,
                        logical_hash=result.logical_hash,
                        normalize_status=result.normalize_status,
                    )
            if on_progress is not None:
                on_progress(metrics)


def _build_work_item(
    row: sqlite3.Row,
    *,
    raw_connection: sqlite3.Connection,
    model_validation_limits: ModelValidationLimits,
    normalize_options: NormalizeOptions,
) -> _WorkItem:
    page_id = row["page_id"]
    return _WorkItem(
        page_id=page_id,
        revision_id=row["revision_id"],
        title=row["title"],
        normalized_title=row["normalized_title"],
        url=row["url"],
        date_modified=row["date_modified"],
        html_zstd=row["html_zstd"],
        aliases=extract_redirect_aliases(raw_connection, page_id),
        categories=_read_categories(raw_connection, page_id),
        media=_read_media(raw_connection, page_id),
        license_ids=_read_license_ids(raw_connection, page_id),
        model_validation_limits=model_validation_limits,
        normalize_options=normalize_options,
    )


def _compute_normalized(item: _WorkItem) -> _ComputedResult:
    """Pure, picklable CPU-bound step: HTML normalization through validation and
    hashing. No database access -- safe to run in a worker process."""
    page_id = item.page_id
    title = item.title

    if item.html_zstd is not None:
        html = decompress(item.html_zstd).decode("utf-8")
        blocks, body_media, pipeline_diagnostics = normalize_html(html, item.normalize_options)
    else:
        blocks, body_media, pipeline_diagnostics = (), (), ()

    stamped_pipeline_diagnostics = tuple(
        _stamp_diagnostic(diagnostic, page_id=page_id, title=title)
        for diagnostic in pipeline_diagnostics
    )

    article = Article(
        page_id=page_id,
        revision_id=item.revision_id,
        title=title,
        normalized_title=item.normalized_title,
        source_url=item.url,
        source_date_modified=datetime.fromisoformat(item.date_modified),
        abstract=_extract_abstract(blocks),
        blocks=blocks,
        aliases=item.aliases,
        categories=item.categories,
        media=(
            select_media(item.media + body_media) if item.normalize_options.images_enabled else ()
        ),
        diagnostics=stamped_pipeline_diagnostics,
        source_license_ids=item.license_ids,
    )

    validation_diagnostics = validate_article(article, item.model_validation_limits)
    article = replace(article, diagnostics=article.diagnostics + validation_diagnostics)

    has_error = any(d.severity in ("error", "fatal") for d in validation_diagnostics)
    if has_error:
        normalize_status = "rejected"
    else:
        normalize_status = "fallback" if _contains_unsupported(article.blocks) else "complete"

    return _ComputedResult(
        article=article,
        canonical_json=encode_article(article),
        logical_hash=compute_logical_hash(article),
        normalize_status=normalize_status,
    )


def _stamp_diagnostic(diagnostic: Diagnostic, *, page_id: int, title: str) -> Diagnostic:
    return Diagnostic(
        code=diagnostic.code,
        severity=diagnostic.severity,
        stage=diagnostic.stage,
        page_id=page_id,
        title=title,
        message=diagnostic.message,
        source_path=diagnostic.source_path,
        source_excerpt=diagnostic.source_excerpt,
        details=diagnostic.details,
    )


def _extract_abstract(blocks: tuple[Block, ...]) -> str | None:
    for block in blocks:
        if isinstance(block, ParagraphBlock):
            text = "".join(_inline_text(inline) for inline in block.inlines).strip()
            return text or None
    return None


def _inline_text(inline: object) -> str:
    value = getattr(inline, "value", None)
    if isinstance(value, str):
        return value
    nested = getattr(inline, "inlines", None)
    if nested is not None:
        return "".join(_inline_text(item) for item in nested)
    return ""


def _contains_unsupported(blocks: tuple[Block, ...]) -> bool:
    for block in blocks:
        if isinstance(block, UnsupportedBlock):
            return True
        if _contains_unsupported(_child_blocks(block)):
            return True
    return False


def _child_blocks(block: Block) -> tuple[Block, ...]:
    children: list[Block] = []
    if isinstance(block, UnorderedListBlock | OrderedListBlock):
        for item in block.items:
            children.extend(item.blocks)
    entries = getattr(block, "entries", None)
    if entries is not None:
        for entry in entries:
            for definition in entry.definitions:
                children.extend(definition)
    if isinstance(block, QuoteBlock):
        children.extend(block.blocks)
    if isinstance(block, TableBlock):
        for row in block.rows:
            for cell in row:
                children.extend(cell.blocks)
    if isinstance(block, InfoboxBlock):
        for field in block.fields:
            children.extend(field.value)
    return tuple(children)


def _read_categories(connection: sqlite3.Connection, page_id: int) -> tuple[str, ...]:
    rows = connection.execute(
        "SELECT category_name FROM categories WHERE page_id = ? ORDER BY ordinal",
        (page_id,),
    ).fetchall()
    return tuple(row["category_name"] for row in rows)


def _read_media(connection: sqlite3.Connection, page_id: int) -> tuple[MediaReference, ...]:
    row = connection.execute(
        "SELECT content_url, width, height FROM main_images WHERE page_id = ?",
        (page_id,),
    ).fetchone()
    if row is None:
        return ()
    return (
        MediaReference(
            media_id=row["content_url"],
            source_url=row["content_url"],
            source_name=None,
            alt_text=None,
            caption=None,
            role="main",
            source_width=row["width"],
            source_height=row["height"],
        ),
    )


def _read_license_ids(connection: sqlite3.Connection, page_id: int) -> tuple[str, ...]:
    rows = connection.execute(
        """
        SELECT licenses.identifier AS identifier
        FROM article_licenses
        JOIN licenses ON licenses.license_id = article_licenses.license_id
        WHERE article_licenses.page_id = ?
        ORDER BY article_licenses.ordinal
        """,
        (page_id,),
    ).fetchall()
    return tuple(row["identifier"] for row in rows)


def _write_manifest(manifest: NormalizeManifest, destination: Path) -> None:
    _write_stage_manifest_payload(manifest.payload(), destination)
