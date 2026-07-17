"""Image plan/fetch/convert orchestration (TASK-O012, ARCHITECTURE.md EPIC O).

Ties TASK-O003-O011 together into three phases matching the CLI's
`image-plan`/`image-fetch`/`image-convert` commands:

- `plan_media` reads every `MediaReference` already selected into
  `model.sqlite3` (TASK-O012 part 1 wired TASK-O001's body-image
  extraction into normalize, so this now includes more than the
  Snapshot's single main image).
- `fetch_media` downloads each *unique* `source_url` once (TASK-O004's
  `SecureMediaDownloader`), sanitizes SVGs (TASK-O006) or validates
  everything else's MIME/magic-bytes/decoded-pixel count (TASK-O005),
  and never raises: a failure for one URL becomes a failed
  `FetchOutcome`, not a crashed run.
- `convert_media` raster-converts each successfully fetched original to
  BMP (TASK-O007) through a content-addressed cache (TASK-O008), then
  drops any result that's a byte-for-byte duplicate of an earlier one
  (TASK-O009).

This intentionally does not use the heavier stage-manifest/resume
machinery `ingest`/`normalize`/`generate` use -- image fetch/convert is
closer in shape to the existing `acquire`/`register-local-source`/
`inspect-source` utility commands (network I/O against external hosts,
not a resumable multi-hour bulk pipeline), so it follows that lighter
pattern instead.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from wikiepwing.media.cache import MediaCache, compute_content_hash
from wikiepwing.media.dedup import HashedMedia, deduplicate_media
from wikiepwing.media.downloader import MediaDownloadError, SecureMediaDownloader
from wikiepwing.media.raster_converter import RasterConversionError, convert_to_bmp
from wikiepwing.media.svg_sanitizer import SvgSanitizeError, sanitize_svg
from wikiepwing.media.validation import MediaValidationError, validate_media_bytes
from wikiepwing.model.article import MediaReference
from wikiepwing.pipeline.atomic_write import atomic_write_bytes, atomic_write_text


@dataclass(frozen=True, slots=True)
class MediaPlanEntry:
    """One `MediaReference` selected for a specific article."""

    page_id: int
    media: MediaReference


def plan_media(model_database_path: Path) -> tuple[MediaPlanEntry, ...]:
    """Read every non-rejected article's selected media from `model.sqlite3`."""
    connection = sqlite3.connect(model_database_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT m.page_id, m.media_id, m.source_url, m.source_name, m.alt_text, "
            "m.caption, m.role, m.source_width, m.source_height "
            "FROM media_references AS m "
            "JOIN articles AS a ON a.page_id = m.page_id "
            "WHERE a.normalize_status != 'rejected' "
            "ORDER BY m.page_id, m.ordinal"
        ).fetchall()
    finally:
        connection.close()

    return tuple(
        MediaPlanEntry(
            page_id=row["page_id"],
            media=MediaReference(
                media_id=row["media_id"],
                source_url=row["source_url"],
                source_name=row["source_name"],
                alt_text=row["alt_text"],
                caption=row["caption"],
                role=row["role"],
                source_width=row["source_width"],
                source_height=row["source_height"],
            ),
        )
        for row in rows
    )


@dataclass(frozen=True, slots=True)
class FetchOutcome:
    """The outcome of fetching one unique `source_url`."""

    source_url: str
    content: bytes | None
    content_hash: str | None
    detected_format: str | None
    error: str | None

    @property
    def ok(self) -> bool:
        """Whether this URL was fetched and validated successfully."""
        return self.content is not None


def fetch_media(
    plan: Sequence[MediaPlanEntry],
    *,
    downloader: SecureMediaDownloader,
    max_pixels: int,
    allow_svg: bool,
    max_workers: int = 1,
    limit: int | None = None,
) -> tuple[FetchOutcome, ...]:
    """Download and validate each unique `source_url` in `plan`, once each.

    `max_workers` (default 1, sequential) fetches multiple URLs concurrently
    via a thread pool -- this is network I/O (each `SecureMediaDownloader.download`
    call already backs off on its own on HTTP 429), so threads are the right
    tool, unlike normalize's CPU-bound process pool. Keep this modest (a
    handful of workers, not `os.cpu_count()`) to stay polite to the single
    upstream host (`upload.wikimedia.org`) rather than hammering it with as
    many concurrent connections as this machine has cores.

    `limit`, if set, stops after attempting the first `limit` unique URLs
    (in `plan` order) rather than every one -- useful for exercising the rest
    of the pipeline (convert, generate, EPWING build) end-to-end without
    waiting for a full-scale fetch to finish first.
    """
    if max_workers < 1:
        raise ValueError("max_workers must be positive")
    if limit is not None and limit < 0:
        raise ValueError("limit must not be negative")

    seen_urls: dict[str, None] = {}
    unique_urls: list[str] = []
    for entry in plan:
        url = entry.media.source_url
        if url in seen_urls:
            continue
        seen_urls[url] = None
        unique_urls.append(url)
        if limit is not None and len(unique_urls) >= limit:
            break

    fetch_one = partial(
        _fetch_one, downloader=downloader, max_pixels=max_pixels, allow_svg=allow_svg
    )
    executor_context = (
        ThreadPoolExecutor(max_workers=max_workers) if max_workers > 1 else nullcontext()
    )
    with executor_context as executor:
        mapper = executor.map if executor is not None else map
        return tuple(mapper(fetch_one, unique_urls))


def _fetch_one(
    url: str, *, downloader: SecureMediaDownloader, max_pixels: int, allow_svg: bool
) -> FetchOutcome:
    try:
        downloaded = downloader.download(url)
    except MediaDownloadError as error:
        return FetchOutcome(
            source_url=url, content=None, content_hash=None, detected_format=None, error=str(error)
        )

    is_svg = downloaded.content_type is not None and "svg" in downloaded.content_type.lower()
    if is_svg:
        if not allow_svg:
            return FetchOutcome(
                source_url=url,
                content=None,
                content_hash=None,
                detected_format=None,
                error="SVG content is disallowed by configuration",
            )
        try:
            sanitized = sanitize_svg(downloaded.content)
        except SvgSanitizeError as error:
            return FetchOutcome(
                source_url=url,
                content=None,
                content_hash=None,
                detected_format=None,
                error=str(error),
            )
        return FetchOutcome(
            source_url=url,
            content=sanitized,
            content_hash=compute_content_hash(sanitized),
            detected_format="svg",
            error=None,
        )

    try:
        validated = validate_media_bytes(
            downloaded.content, declared_content_type=downloaded.content_type, max_pixels=max_pixels
        )
    except MediaValidationError as error:
        return FetchOutcome(
            source_url=url, content=None, content_hash=None, detected_format=None, error=str(error)
        )
    return FetchOutcome(
        source_url=url,
        content=downloaded.content,
        content_hash=compute_content_hash(downloaded.content),
        detected_format=validated.detected_format,
        error=None,
    )


@dataclass(frozen=True, slots=True)
class ConvertOutcome:
    """One successfully converted, deduplicated graphic ready for TASK-O011."""

    source_url: str
    content_hash: str
    bmp_bytes: bytes


def convert_media(
    fetch_outcomes: Sequence[FetchOutcome], *, cache: MediaCache
) -> tuple[ConvertOutcome, ...]:
    """Raster-convert every successful fetch to BMP, then drop duplicate content."""
    hashed: list[HashedMedia] = []
    converted_by_source_url: dict[str, tuple[str, bytes]] = {}
    for outcome in fetch_outcomes:
        if not outcome.ok:
            continue
        assert outcome.content is not None
        assert outcome.content_hash is not None
        assert outcome.detected_format is not None

        content = outcome.content
        content_hash = outcome.content_hash
        source_format = outcome.detected_format

        def _convert(content: bytes = content, source_format: str = source_format) -> bytes:
            return convert_to_bmp(content, source_format=source_format)

        try:
            bmp_bytes = cache.get_or_convert(content_hash, convert=_convert)
        except RasterConversionError:
            continue

        converted_by_source_url[outcome.source_url] = (content_hash, bmp_bytes)
        hashed.append(
            HashedMedia(media=_placeholder_media(outcome.source_url), content_hash=content_hash)
        )

    return tuple(
        ConvertOutcome(
            source_url=media.source_url,
            content_hash=converted_by_source_url[media.source_url][0],
            bmp_bytes=converted_by_source_url[media.source_url][1],
        )
        for media in deduplicate_media(hashed)
    )


def _placeholder_media(source_url: str) -> MediaReference:
    return MediaReference(
        media_id=source_url,
        source_url=source_url,
        source_name=None,
        alt_text=None,
        caption=None,
        role="unknown",
        source_width=None,
        source_height=None,
    )


def write_fetch_report(
    outcomes: Sequence[FetchOutcome], *, originals_dir: Path, report_path: Path
) -> None:
    """Persist `outcomes` to `report_path`, storing each successful fetch's bytes by content hash.

    `image-convert` (a separate CLI invocation, possibly a separate process
    entirely) reads this report and `originals_dir` back via
    `read_fetch_report` rather than re-downloading anything.
    """
    originals_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for outcome in outcomes:
        if outcome.ok:
            assert outcome.content is not None and outcome.content_hash is not None
            atomic_write_bytes(originals_dir / f"{outcome.content_hash}.bin", outcome.content)
        records.append(
            {
                "source_url": outcome.source_url,
                "content_hash": outcome.content_hash,
                "detected_format": outcome.detected_format,
                "ok": outcome.ok,
                "error": outcome.error,
            }
        )
    atomic_write_text(
        report_path, json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def read_fetch_report(report_path: Path, *, originals_dir: Path) -> tuple[FetchOutcome, ...]:
    """Reconstruct the `FetchOutcome`s a prior `write_fetch_report` call persisted."""
    records = json.loads(report_path.read_text(encoding="utf-8"))
    outcomes: list[FetchOutcome] = []
    for record in records:
        content: bytes | None = None
        if record["ok"]:
            content = (originals_dir / f"{record['content_hash']}.bin").read_bytes()
        outcomes.append(
            FetchOutcome(
                source_url=record["source_url"],
                content=content,
                content_hash=record["content_hash"],
                detected_format=record["detected_format"],
                error=record["error"],
            )
        )
    return tuple(outcomes)
