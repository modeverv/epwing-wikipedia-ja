"""Normalize orchestration: read accepted raw articles, normalize, validate, write model.sqlite3.

Mirrors `wikiepwing.ingest.orchestrate`'s manifest lifecycle (running/complete/
failed, `--force`) for the normalize stage (TASK-G012).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from wikiepwing.ingest.database import connect_raw_database
from wikiepwing.ingest.zstd_codec import decompress
from wikiepwing.links.redirect_aliases import extract_redirect_aliases
from wikiepwing.model.article import Article, MediaReference
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
from wikiepwing.normalize.pipeline import NormalizeOptions, normalize_html
from wikiepwing.pipeline.fingerprint import compute_input_fingerprint
from wikiepwing.pipeline.stage_manifest import StageManifestError
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
    git_commit: str | None = None,
    force: bool = False,
    on_progress: Callable[[NormalizeMetrics], None] | None = None,
) -> NormalizeResult:
    """Normalize every accepted raw article into model.sqlite3."""
    if batch_size < 1:
        raise NormalizeError("batch_size must be positive")
    previous_status = read_manifest_status(manifest_path)
    if previous_status == "running" and not force:
        raise NormalizeError(
            f"manifest {manifest_path} shows a previous run still 'running'; "
            "pass force=True to proceed after confirming that run is dead"
        )
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
        ),
        manifest_path,
    )

    database_path = initialize_model_database(model_database_path, model_migrations_path)
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
        )
        _write_manifest(manifest, manifest_path)

    return NormalizeResult(
        manifest=manifest, manifest_path=manifest_path, model_database_path=database_path
    )


def _manifest_inputs(raw_database_path: Path) -> dict[str, str]:
    inputs = {"raw_database_path": str(raw_database_path)}
    if raw_database_path.is_file():
        inputs["raw_database_fingerprint"] = compute_input_fingerprint(raw_database_path)
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
) -> NormalizeManifest:
    outputs: tuple[dict[str, object], ...] = ()
    if model_database_path is not None and model_database_path.is_file():
        fingerprint = compute_fingerprint(model_database_path)
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
        inputs=_manifest_inputs(raw_database_path),
        outputs=outputs,
        metrics=metrics,
        software={
            "git_commit": git_commit,
            "app_image_digest": None,
            "toolchain_image_digest": None,
        },
    )


def _normalize_all(
    raw_connection: sqlite3.Connection,
    *,
    repository: ModelRepository,
    metrics: NormalizeMetrics,
    model_validation_limits: ModelValidationLimits,
    normalize_options: NormalizeOptions,
    batch_size: int,
    on_progress: Callable[[NormalizeMetrics], None] | None,
) -> None:
    cursor = raw_connection.execute(
        "SELECT page_id, revision_id, title, normalized_title, url, date_modified, html_zstd "
        "FROM articles WHERE ingest_status = 'accepted' AND is_deleted = 0 ORDER BY page_id"
    )
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            return
        with repository.batch():
            for row in rows:
                _normalize_one(
                    row,
                    raw_connection=raw_connection,
                    repository=repository,
                    metrics=metrics,
                    model_validation_limits=model_validation_limits,
                    normalize_options=normalize_options,
                )
        if on_progress is not None:
            on_progress(metrics)


def _normalize_one(
    row: sqlite3.Row,
    *,
    raw_connection: sqlite3.Connection,
    repository: ModelRepository,
    metrics: NormalizeMetrics,
    model_validation_limits: ModelValidationLimits,
    normalize_options: NormalizeOptions,
) -> None:
    metrics.articles_read += 1
    page_id = row["page_id"]
    title = row["title"]

    if row["html_zstd"] is not None:
        html = decompress(row["html_zstd"]).decode("utf-8")
        blocks, pipeline_diagnostics = normalize_html(html, normalize_options)
    else:
        blocks, pipeline_diagnostics = (), ()

    stamped_pipeline_diagnostics = tuple(
        _stamp_diagnostic(diagnostic, page_id=page_id, title=title)
        for diagnostic in pipeline_diagnostics
    )

    article = Article(
        page_id=page_id,
        revision_id=row["revision_id"],
        title=title,
        normalized_title=row["normalized_title"],
        source_url=row["url"],
        source_date_modified=datetime.fromisoformat(row["date_modified"]),
        abstract=_extract_abstract(blocks),
        blocks=blocks,
        aliases=extract_redirect_aliases(raw_connection, page_id),
        categories=_read_categories(raw_connection, page_id),
        media=_read_media(raw_connection, page_id),
        diagnostics=stamped_pipeline_diagnostics,
        source_license_ids=_read_license_ids(raw_connection, page_id),
    )

    validation_diagnostics = validate_article(article, model_validation_limits)
    article = replace(article, diagnostics=article.diagnostics + validation_diagnostics)

    for diagnostic in article.diagnostics:
        if diagnostic.severity == "warning":
            metrics.warnings += 1
        elif diagnostic.severity == "error":
            metrics.errors += 1
        elif diagnostic.severity == "fatal":
            metrics.fatals += 1

    has_error = any(d.severity in ("error", "fatal") for d in validation_diagnostics)
    if has_error:
        normalize_status = "rejected"
        metrics.articles_rejected += 1
    else:
        normalize_status = "fallback" if _contains_unsupported(article.blocks) else "complete"
        metrics.articles_written += 1

    repository.write_article(
        article,
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
