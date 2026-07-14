"""Raw database verifier: integrity, foreign keys, table counts, sample decompression."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from wikiepwing.ingest.zstd_codec import ZstdCodecError, decompress

DEFAULT_SAMPLE_SIZE = 20

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
    connection: sqlite3.Connection, *, sample_size: int = DEFAULT_SAMPLE_SIZE
) -> RawVerificationResult:
    """Verify integrity, foreign keys, table counts, and a sample of compressed bodies."""
    if sample_size < 0:
        raise ValueError("sample_size must not be negative")
    integrity_row = connection.execute("PRAGMA integrity_check").fetchone()
    integrity_check = "no result" if integrity_row is None else str(integrity_row[0])
    foreign_key_errors = len(connection.execute("PRAGMA foreign_key_check").fetchall())
    counts = _collect_counts(connection)
    sample_checked, sample_failures = _verify_sample_decompression(connection, sample_size)
    return RawVerificationResult(
        integrity_check=integrity_check,
        foreign_key_errors=foreign_key_errors,
        counts=counts,
        sample_checked=sample_checked,
        sample_failures=tuple(sample_failures),
    )


def _collect_counts(connection: sqlite3.Connection) -> RawVerificationCounts:
    values = {key: connection.execute(query).fetchone()[0] for key, query in _COUNT_QUERIES.items()}
    return RawVerificationCounts(**values)


def _verify_sample_decompression(
    connection: sqlite3.Connection, sample_size: int
) -> tuple[int, list[str]]:
    if sample_size == 0:
        return 0, []
    total = connection.execute(
        "SELECT COUNT(*) FROM articles "
        "WHERE ingest_status = 'accepted' AND (html_zstd IS NOT NULL OR wikitext_zstd IS NOT NULL)"
    ).fetchone()[0]
    if total == 0:
        return 0, []
    stride = max(1, total // sample_size)
    rows = connection.execute(
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
    ).fetchall()

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
    return checked, failures
