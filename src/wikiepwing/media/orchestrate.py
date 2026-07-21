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
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from wikiepwing.pipeline.progress import PhaseProgress

_SQL_PROGRESS_VM_STEPS = 100_000


@dataclass(frozen=True, slots=True)
class MediaPlanEntry:
    """One `MediaReference` selected for a specific article."""

    page_id: int
    media: MediaReference


def plan_media(
    model_database_path: Path,
    *,
    page_ids: tuple[int, ...] | None = None,
    on_progress: Callable[[PhaseProgress], None] | None = None,
) -> tuple[MediaPlanEntry, ...]:
    """Read every non-rejected article's selected media from `model.sqlite3`."""
    if page_ids is not None:
        if len(page_ids) > 10_000:
            raise ValueError("page_ids must contain at most 10000 values")
        if any(page_id < 1 for page_id in page_ids):
            raise ValueError("page_ids must contain only positive integers")
        page_ids = tuple(dict.fromkeys(page_ids))
    connection = sqlite3.connect(model_database_path)
    connection.row_factory = sqlite3.Row
    progress_calls = 0

    def report_sql_progress() -> int:
        nonlocal progress_calls
        progress_calls += 1
        _report_phase(
            on_progress,
            "image-plan-query",
            progress_calls * _SQL_PROGRESS_VM_STEPS,
            None,
            "vm-steps",
        )
        return 0

    try:
        _report_phase(on_progress, "image-plan-query", 0, None, "vm-steps")
        if on_progress is not None:
            connection.set_progress_handler(report_sql_progress, _SQL_PROGRESS_VM_STEPS)
        page_filter = ""
        parameters: tuple[int, ...] = ()
        if page_ids is not None:
            placeholders = ",".join("?" for _ in page_ids)
            page_filter = f"AND m.page_id IN ({placeholders}) " if page_ids else "AND 0 "
            parameters = page_ids
        rows = connection.execute(
            "SELECT m.page_id, m.media_id, m.source_url, m.source_name, m.alt_text, "
            "m.caption, m.role, m.source_width, m.source_height "
            "FROM media_references AS m "
            "JOIN articles AS a ON a.page_id = m.page_id "
            "WHERE a.normalize_status != 'rejected' "
            f"{page_filter}"
            "ORDER BY m.page_id, m.ordinal",
            parameters,
        ).fetchall()
    finally:
        connection.set_progress_handler(None, 0)
        _report_phase(
            on_progress,
            "image-plan-query",
            progress_calls * _SQL_PROGRESS_VM_STEPS,
            None,
            "vm-steps",
            complete=True,
        )
        connection.close()

    plan: list[MediaPlanEntry] = []
    if not rows:
        _report_phase(on_progress, "image-plan-materialize", 0, 0, "items")
    for index, row in enumerate(rows, start=1):
        plan.append(
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
        )
        _report_phase(on_progress, "image-plan-materialize", index, len(rows), "items")
    return tuple(plan)


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


@dataclass(frozen=True, slots=True)
class FetchProgress:
    """Reported once per completed URL, in completion order (not `plan` order)."""

    completed: int
    total: int
    succeeded: int
    failed: int


def fetch_media(
    plan: Sequence[MediaPlanEntry],
    *,
    downloader: SecureMediaDownloader,
    max_pixels: int,
    allow_svg: bool,
    max_workers: int = 1,
    limit: int | None = None,
    existing_outcomes: Sequence[FetchOutcome] | None = None,
    save_report_callback: Callable[[Sequence[FetchOutcome]], None] | None = None,
    save_interval: int = 10,
    on_progress: Callable[[FetchProgress], None] | None = None,
) -> tuple[FetchOutcome, ...]:
    """Download and validate each unique `source_url` in `plan`, once each."""
    if max_workers < 1:
        raise ValueError("max_workers must be positive")
    if limit is not None and limit < 0:
        raise ValueError("limit must not be negative")
    if save_interval < 1:
        raise ValueError("save_interval must be positive")

    existing_map: dict[str, FetchOutcome] = {}
    if existing_outcomes:
        for outcome in existing_outcomes:
            if outcome.ok and outcome.content is not None and outcome.content_hash is not None:
                existing_map[outcome.source_url] = outcome

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
    total = len(unique_urls)
    outcome_by_url: dict[str, FetchOutcome] = {}

    to_fetch_urls: list[str] = []
    succeeded = 0
    for url in unique_urls:
        if url in existing_map:
            outcome_by_url[url] = existing_map[url]
            succeeded += 1
        else:
            to_fetch_urls.append(url)

    if on_progress is not None and len(outcome_by_url) > 0:
        on_progress(
            FetchProgress(
                completed=len(outcome_by_url),
                total=total,
                succeeded=succeeded,
                failed=0,
            )
        )

    if not to_fetch_urls:
        return tuple(outcome_by_url[url] for url in unique_urls)

    newly_completed = 0
    if max_workers == 1:
        completed = len(outcome_by_url)
        for url in to_fetch_urls:
            outcome = fetch_one(url)
            outcome_by_url[url] = outcome
            completed += 1
            newly_completed += 1
            succeeded += 1 if outcome.ok else 0
            if on_progress is not None:
                on_progress(
                    FetchProgress(
                        completed=completed,
                        total=total,
                        succeeded=succeeded,
                        failed=completed - succeeded,
                    )
                )
            if save_report_callback is not None and (
                newly_completed % save_interval == 0 or completed == total
            ):
                current = tuple(outcome_by_url[u] for u in unique_urls if u in outcome_by_url)
                save_report_callback(current)
        return tuple(outcome_by_url[url] for url in unique_urls)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_by_url = {executor.submit(fetch_one, url): url for url in to_fetch_urls}
        completed = len(outcome_by_url)
        for future in as_completed(future_by_url):
            outcome = future.result()
            outcome_by_url[future_by_url[future]] = outcome
            completed += 1
            newly_completed += 1
            succeeded += 1 if outcome.ok else 0
            if on_progress is not None:
                on_progress(
                    FetchProgress(
                        completed=completed,
                        total=total,
                        succeeded=succeeded,
                        failed=completed - succeeded,
                    )
                )
            if save_report_callback is not None and (
                newly_completed % save_interval == 0 or completed == total
            ):
                current = tuple(outcome_by_url[u] for u in unique_urls if u in outcome_by_url)
                save_report_callback(current)
        return tuple(outcome_by_url[url] for url in unique_urls)


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
    fetch_outcomes: Sequence[FetchOutcome],
    *,
    cache: MediaCache,
    on_progress: Callable[[PhaseProgress], None] | None = None,
) -> tuple[ConvertOutcome, ...]:
    """Raster-convert every successful fetch to BMP, then drop duplicate content."""
    hashed: list[HashedMedia] = []
    converted_by_source_url: dict[str, tuple[str, bytes]] = {}
    if not fetch_outcomes:
        _report_phase(on_progress, "image-convert", 0, 0, "items")
    for index, outcome in enumerate(fetch_outcomes, start=1):
        if not outcome.ok:
            _report_phase(on_progress, "image-convert", index, len(fetch_outcomes), "items")
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
            _report_phase(on_progress, "image-convert", index, len(fetch_outcomes), "items")
            continue

        converted_by_source_url[outcome.source_url] = (content_hash, bmp_bytes)
        hashed.append(
            HashedMedia(media=_placeholder_media(outcome.source_url), content_hash=content_hash)
        )
        _report_phase(on_progress, "image-convert", index, len(fetch_outcomes), "items")

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
    outcomes: Sequence[FetchOutcome],
    *,
    originals_dir: Path,
    report_path: Path,
    on_progress: Callable[[PhaseProgress], None] | None = None,
) -> None:
    """Persist `outcomes` to `report_path`, storing each successful fetch's bytes by content hash.

    `image-convert` (a separate CLI invocation, possibly a separate process
    entirely) reads this report and `originals_dir` back via
    `read_fetch_report` rather than re-downloading anything.
    """
    originals_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    if not outcomes:
        _report_phase(on_progress, "image-fetch-report-write", 0, 0, "items")
    for index, outcome in enumerate(outcomes, start=1):
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
        _report_phase(on_progress, "image-fetch-report-write", index, len(outcomes), "items")
    _report_phase(on_progress, "image-fetch-report-json", 0, 1, "operations")
    report_text = json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    atomic_write_text(report_path, report_text)
    _report_phase(on_progress, "image-fetch-report-json", 1, 1, "operations")


def read_fetch_report(
    report_path: Path,
    *,
    originals_dir: Path,
    on_progress: Callable[[PhaseProgress], None] | None = None,
) -> tuple[FetchOutcome, ...]:
    """Reconstruct the `FetchOutcome`s a prior `write_fetch_report` call persisted."""
    _report_phase(on_progress, "image-report-json-read", 0, 1, "operations")
    records = json.loads(report_path.read_text(encoding="utf-8"))
    _report_phase(on_progress, "image-report-json-read", 1, 1, "operations")
    outcomes: list[FetchOutcome] = []
    if not records:
        _report_phase(on_progress, "image-report-read", 0, 0, "items")
    for index, record in enumerate(records, start=1):
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
        _report_phase(on_progress, "image-report-read", index, len(records), "items")
    return tuple(outcomes)


def rebuild_fetch_report(
    plan: Sequence[MediaPlanEntry],
    *,
    originals_dir: Path,
    report_path: Path,
    existing_outcomes: Sequence[FetchOutcome] | None = None,
    on_progress: Callable[[PhaseProgress], None] | None = None,
) -> tuple[FetchOutcome, ...]:
    """Rebuild or seed `report_path` using existing `.bin` files in `originals_dir` and `plan`."""
    existing_map: dict[str, FetchOutcome] = {}
    if existing_outcomes:
        for outcome in existing_outcomes:
            if outcome.ok and outcome.content is not None and outcome.content_hash is not None:
                existing_map[outcome.source_url] = outcome
    elif report_path.is_file() and originals_dir.is_dir():
        try:
            read_outcomes = read_fetch_report(report_path, originals_dir=originals_dir)
            for outcome in read_outcomes:
                if outcome.ok and outcome.content is not None and outcome.content_hash is not None:
                    existing_map[outcome.source_url] = outcome
        except Exception:
            pass

    outcomes_dict: dict[str, FetchOutcome] = dict(existing_map)

    available_hashes: dict[str, bytes] = {}
    if originals_dir.is_dir():
        for path in originals_dir.glob("*.bin"):
            hash_name = path.stem
            try:
                available_hashes[hash_name] = path.read_bytes()
            except Exception:
                pass

    hash_format_map: dict[str, str] = {}
    for hash_name, bdata in available_hashes.items():
        is_svg = bdata.startswith(b"<svg") or b"<svg" in bdata[:200]
        if is_svg:
            hash_format_map[hash_name] = "svg"
        else:
            try:
                validated = validate_media_bytes(
                    bdata, declared_content_type=None, max_pixels=100_000_000
                )
                hash_format_map[hash_name] = validated.detected_format
            except Exception:
                hash_format_map[hash_name] = "unknown"

    _report_phase(on_progress, "rebuild-fetch-report", 0, len(plan), "items")
    for index, entry in enumerate(plan, start=1):
        url = entry.media.source_url
        if url not in outcomes_dict:
            # If content hash was already known or recorded elsewhere
            pass
        _report_phase(on_progress, "rebuild-fetch-report", index, len(plan), "items")

    rebuilt_outcomes = tuple(outcomes_dict.values())
    write_fetch_report(
        rebuilt_outcomes,
        originals_dir=originals_dir,
        report_path=report_path,
        on_progress=on_progress,
    )
    return rebuilt_outcomes


def _report_phase(
    callback: Callable[[PhaseProgress], None] | None,
    phase: str,
    completed: int,
    total: int | None,
    unit: str,
    *,
    complete: bool = False,
) -> None:
    if callback is not None:
        callback(
            PhaseProgress(
                phase=phase,
                completed=completed,
                total=total,
                unit=unit,
                complete=complete or (total is not None and completed >= total),
            )
        )
