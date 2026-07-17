"""Raw database verifier: integrity, foreign keys, table counts, sample decompression."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import TypeVar, cast

from wikiepwing.ingest.zstd_codec import ZstdCodecError, decompress
from wikiepwing.pipeline.progress import PhaseProgress

DEFAULT_SAMPLE_SIZE = 20
_SQL_PROGRESS_VM_STEPS = 100_000
_T = TypeVar("_T")

_COUNT_QUERIES = {
    "accepted_articles": "SELECT COUNT(*) FROM articles WHERE ingest_status = 'accepted'",
    "rejected_articles": "SELECT COUNT(*) FROM articles WHERE ingest_status = 'rejected'",
    "redirects": "SELECT COUNT(*) FROM redirects",
    "categories": "SELECT COUNT(*) FROM categories",
    "templates": "SELECT COUNT(*) FROM templates",
    "licenses": "SELECT COUNT(*) FROM licenses",
    "article_licenses": "SELECT COUNT(*) FROM article_licenses",
    "main_images": "SELECT COUNT(*) FROM main_images",
    "ingest_duplicates": "SELECT COUNT(*) FROM ingest_duplicates",
    "diagnostics": "SELECT COUNT(*) FROM diagnostics",
}


@dataclass(frozen=True, slots=True)
class RawVerificationCounts:
    """Row counts across every table the raw ingest pipeline writes."""

    accepted_articles: int
    rejected_articles: int
    redirects: int
    categories: int
    templates: int
    licenses: int
    article_licenses: int
    main_images: int
    ingest_duplicates: int
    diagnostics: int

    def payload(self) -> dict[str, int]:
        """Return these counts as a JSON-serializable mapping."""
        return {
            "accepted_articles": self.accepted_articles,
            "rejected_articles": self.rejected_articles,
            "redirects": self.redirects,
            "categories": self.categories,
            "templates": self.templates,
            "licenses": self.licenses,
            "article_licenses": self.article_licenses,
            "main_images": self.main_images,
            "ingest_duplicates": self.ingest_duplicates,
            "diagnostics": self.diagnostics,
        }


@dataclass(frozen=True, slots=True)
class RawVerificationResult:
    """The outcome of verifying one raw.sqlite3 database."""

    integrity_check: str
    foreign_key_errors: int
    counts: RawVerificationCounts
    sample_checked: int
    sample_failures: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Return True only if integrity, foreign keys, and every sample all passed."""
        return (
            self.integrity_check == "ok"
            and self.foreign_key_errors == 0
            and not self.sample_failures
        )

    def payload(self) -> dict[str, object]:
        """Return this result as a JSON-serializable mapping."""
        return {
            "ok": self.ok,
            "integrity_check": self.integrity_check,
            "foreign_key_errors": self.foreign_key_errors,
            "counts": self.counts.payload(),
            "sample_checked": self.sample_checked,
            "sample_failures": list(self.sample_failures),
        }


def verify_raw_database(
    connection: sqlite3.Connection,
    *,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    on_progress: Callable[[PhaseProgress], None] | None = None,
) -> RawVerificationResult:
    """Verify integrity, foreign keys, table counts, and a sample of compressed bodies."""
    if sample_size < 0:
        raise ValueError("sample_size must not be negative")
    integrity_row = _run_sql_phase(
        connection,
        "verify-raw-integrity",
        on_progress,
        lambda: connection.execute("PRAGMA integrity_check").fetchone(),
    )
    integrity_check = "no result" if integrity_row is None else str(integrity_row[0])
    foreign_key_errors = len(
        _run_sql_phase(
            connection,
            "verify-raw-foreign-keys",
            on_progress,
            lambda: connection.execute("PRAGMA foreign_key_check").fetchall(),
        )
    )
    counts = _collect_counts(connection, on_progress=on_progress)
    sample_checked, sample_failures = _verify_sample_decompression(
        connection, sample_size, on_progress=on_progress
    )
    return RawVerificationResult(
        integrity_check=integrity_check,
        foreign_key_errors=foreign_key_errors,
        counts=counts,
        sample_checked=sample_checked,
        sample_failures=tuple(sample_failures),
    )


def _collect_counts(
    connection: sqlite3.Connection,
    *,
    on_progress: Callable[[PhaseProgress], None] | None,
) -> RawVerificationCounts:
    values = {}
    for key, query in _COUNT_QUERIES.items():
        row = _run_sql_phase(
            connection,
            f"verify-raw-count-{key}",
            on_progress,
            partial(_fetch_count, connection, query),
        )
        assert row is not None
        values[key] = row[0]
    return RawVerificationCounts(**values)


def _fetch_count(connection: sqlite3.Connection, query: str) -> sqlite3.Row | None:
    return cast(sqlite3.Row | None, connection.execute(query).fetchone())


def _verify_sample_decompression(
    connection: sqlite3.Connection,
    sample_size: int,
    *,
    on_progress: Callable[[PhaseProgress], None] | None,
) -> tuple[int, list[str]]:
    if sample_size == 0:
        return 0, []
    total_row = _run_sql_phase(
        connection,
        "verify-raw-sample-count",
        on_progress,
        lambda: connection.execute(
            "SELECT COUNT(*) FROM articles "
            "WHERE ingest_status = 'accepted' "
            "AND (html_zstd IS NOT NULL OR wikitext_zstd IS NOT NULL)"
        ).fetchone(),
    )
    assert total_row is not None
    total = total_row[0]
    if total == 0:
        return 0, []
    stride = max(1, total // sample_size)
    rows = _run_sql_phase(
        connection,
        "verify-raw-sample-select",
        on_progress,
        lambda: connection.execute(
            """
            SELECT page_id, html_zstd, wikitext_zstd FROM (
                SELECT page_id, html_zstd, wikitext_zstd,
                       ROW_NUMBER() OVER (ORDER BY page_id) AS row_number
                FROM articles
                WHERE ingest_status = 'accepted'
                  AND (html_zstd IS NOT NULL OR wikitext_zstd IS NOT NULL)
            )
            WHERE (row_number - 1) % ? = 0
            ORDER BY page_id
            LIMIT ?
            """,
            (stride, sample_size),
        ).fetchall(),
    )

    failures: list[str] = []
    checked = 0
    for row in rows:
        page_id, html_zstd, wikitext_zstd = row[0], row[1], row[2]
        for field, blob in (("html", html_zstd), ("wikitext", wikitext_zstd)):
            if blob is None:
                continue
            checked += 1
            try:
                decompress(blob)
            except ZstdCodecError as error:
                failures.append(f"page_id={page_id} field={field}: {error}")
        if on_progress is not None:
            on_progress(
                PhaseProgress(
                    phase="verify-raw-sample-decompression",
                    completed=checked,
                    total=len(rows) * 2,
                    unit="items",
                )
            )
    if on_progress is not None:
        on_progress(
            PhaseProgress(
                phase="verify-raw-sample-decompression",
                completed=checked,
                total=checked,
                unit="items",
                complete=True,
            )
        )
    return checked, failures


def _run_sql_phase(
    connection: sqlite3.Connection,
    phase: str,
    callback: Callable[[PhaseProgress], None] | None,
    operation: Callable[[], _T],
) -> _T:
    progress_calls = 0

    def report() -> int:
        nonlocal progress_calls
        progress_calls += 1
        if callback is not None:
            callback(
                PhaseProgress(
                    phase=phase,
                    completed=progress_calls * _SQL_PROGRESS_VM_STEPS,
                    total=None,
                    unit="vm-steps",
                )
            )
        return 0

    if callback is not None:
        callback(PhaseProgress(phase=phase, completed=0, total=None, unit="vm-steps"))
        connection.set_progress_handler(report, _SQL_PROGRESS_VM_STEPS)
    try:
        return operation()
    finally:
        connection.set_progress_handler(None, 0)
        if callback is not None:
            callback(
                PhaseProgress(
                    phase=phase,
                    completed=progress_calls * _SQL_PROGRESS_VM_STEPS,
                    total=None,
                    unit="vm-steps",
                    complete=True,
                )
            )
