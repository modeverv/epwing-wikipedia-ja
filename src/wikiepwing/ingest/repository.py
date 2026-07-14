"""Batch SQLite repository writer for raw.sqlite3: transactions, prepared SQL, FK order."""

from __future__ import annotations

import json
import sqlite3
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager

from wikiepwing.ingest.deduplicate import DuplicateRecord, ExistingArticleState
from wikiepwing.ingest.record_parser import LicenseRecord, RawArticle
from wikiepwing.ingest.validate import Diagnostic
from wikiepwing.ingest.zstd_codec import compress


class RawRepositoryError(RuntimeError):
    """Raised when a raw repository write cannot proceed safely."""


def normalize_title(title: str) -> str:
    """Apply the baseline title normalization used for lookups (NFKC, trimmed)."""
    return unicodedata.normalize("NFKC", title).strip()


class RawRepository:
    """Prepared-statement writer for one raw.sqlite3 connection."""

    def __init__(self, connection: sqlite3.Connection, *, zstd_level: int = 6) -> None:
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise RawRepositoryError("connection must have PRAGMA foreign_keys enabled")
        self._connection = connection
        self._zstd_level = zstd_level

    @contextmanager
    def batch(self) -> Iterator[None]:
        """Run a batch of writes inside one transaction, committing or rolling back atomically."""
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()

    def get_existing_accepted(self, page_id: int) -> ExistingArticleState | None:
        """Return the current accepted state for `page_id`, if any."""
        row = self._connection.execute(
            "SELECT revision_id, source_hash, source_sequence FROM articles "
            "WHERE page_id = ? AND ingest_status = 'accepted'",
            (page_id,),
        ).fetchone()
        if row is None:
            return None
        return ExistingArticleState(revision_id=row[0], source_hash=row[1], source_sequence=row[2])

    def write_accepted_article(self, article: RawArticle) -> None:
        """Upsert an accepted article and replace its child rows (redirects, etc.)."""
        html_blob = (
            compress(article.html.encode("utf-8"), level=self._zstd_level)
            if article.html is not None
            else None
        )
        wikitext_blob = (
            compress(article.wikitext.encode("utf-8"), level=self._zstd_level)
            if article.wikitext is not None
            else None
        )
        self._connection.execute(
            """
            INSERT INTO articles (
                page_id, revision_id, title, normalized_title, namespace_id, url,
                date_modified, html_zstd, wikitext_zstd, source_hash, source_sequence,
                ingest_status, is_deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'accepted', 0)
            ON CONFLICT(page_id) DO UPDATE SET
                revision_id = excluded.revision_id,
                title = excluded.title,
                normalized_title = excluded.normalized_title,
                namespace_id = excluded.namespace_id,
                url = excluded.url,
                date_modified = excluded.date_modified,
                html_zstd = excluded.html_zstd,
                wikitext_zstd = excluded.wikitext_zstd,
                source_hash = excluded.source_hash,
                source_sequence = excluded.source_sequence,
                ingest_status = 'accepted',
                is_deleted = 0
            """,
            (
                article.page_id,
                article.revision_id,
                article.title,
                normalize_title(article.title),
                article.namespace_id,
                article.url,
                article.date_modified.isoformat(),
                html_blob,
                wikitext_blob,
                article.source_hash,
                article.source_sequence,
            ),
        )
        self._replace_children(article)

    def write_rejected_article(self, article: RawArticle) -> None:
        """Upsert a rejected article stub: no body blobs, no child rows."""
        self._delete_children(article.page_id)
        self._connection.execute(
            """
            INSERT INTO articles (
                page_id, revision_id, title, normalized_title, namespace_id, url,
                date_modified, html_zstd, wikitext_zstd, source_hash, source_sequence,
                ingest_status, is_deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, 'rejected', 0)
            ON CONFLICT(page_id) DO UPDATE SET
                revision_id = excluded.revision_id,
                title = excluded.title,
                normalized_title = excluded.normalized_title,
                namespace_id = excluded.namespace_id,
                url = excluded.url,
                date_modified = excluded.date_modified,
                html_zstd = NULL,
                wikitext_zstd = NULL,
                source_hash = excluded.source_hash,
                source_sequence = excluded.source_sequence,
                ingest_status = 'rejected',
                is_deleted = 0
            """,
            (
                article.page_id,
                article.revision_id,
                article.title,
                normalize_title(article.title),
                article.namespace_id,
                article.url,
                article.date_modified.isoformat(),
                article.source_hash,
                article.source_sequence,
            ),
        )

    def write_duplicate(self, record: DuplicateRecord) -> None:
        """Append one row to `ingest_duplicates`."""
        self._connection.execute(
            """
            INSERT INTO ingest_duplicates (
                page_id, kept_revision_id, dropped_revision_id, kept_hash, dropped_hash,
                reason, source_sequence
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.page_id,
                record.kept_revision_id,
                record.dropped_revision_id,
                record.kept_hash,
                record.dropped_hash,
                record.reason,
                record.source_sequence,
            ),
        )

    def write_diagnostic(
        self,
        diagnostic: Diagnostic,
        *,
        stage: str,
        page_id: int | None = None,
        title: str | None = None,
    ) -> None:
        """Append one row to `diagnostics`."""
        self._connection.execute(
            """
            INSERT INTO diagnostics (code, severity, stage, page_id, title, message, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                diagnostic.code,
                diagnostic.severity,
                stage,
                page_id,
                title,
                diagnostic.message,
                json.dumps(diagnostic.details, ensure_ascii=False, sort_keys=True),
            ),
        )

    def _delete_children(self, page_id: int) -> None:
        self._connection.execute("DELETE FROM redirects WHERE target_page_id = ?", (page_id,))
        self._connection.execute("DELETE FROM categories WHERE page_id = ?", (page_id,))
        self._connection.execute("DELETE FROM templates WHERE page_id = ?", (page_id,))
        self._connection.execute("DELETE FROM article_licenses WHERE page_id = ?", (page_id,))
        self._connection.execute("DELETE FROM main_images WHERE page_id = ?", (page_id,))

    def _replace_children(self, article: RawArticle) -> None:
        page_id = article.page_id
        self._delete_children(page_id)
        for ordinal, name in enumerate(article.redirects):
            self._connection.execute(
                """
                INSERT INTO redirects (
                    target_page_id, redirect_title, normalized_redirect_title, ordinal
                ) VALUES (?, ?, ?, ?)
                """,
                (page_id, name, normalize_title(name), ordinal),
            )
        for ordinal, name in enumerate(article.categories):
            self._connection.execute(
                """
                INSERT INTO categories (page_id, category_name, normalized_category_name, ordinal)
                VALUES (?, ?, ?, ?)
                """,
                (page_id, name, normalize_title(name), ordinal),
            )
        for ordinal, name in enumerate(article.templates):
            self._connection.execute(
                """
                INSERT INTO templates (page_id, template_name, normalized_template_name, ordinal)
                VALUES (?, ?, ?, ?)
                """,
                (page_id, name, normalize_title(name), ordinal),
            )
        for ordinal, license_record in enumerate(article.licenses):
            license_id = self._get_or_create_license(license_record)
            self._connection.execute(
                "INSERT INTO article_licenses (page_id, license_id, ordinal) VALUES (?, ?, ?)",
                (page_id, license_id, ordinal),
            )
        if article.main_image is not None:
            self._connection.execute(
                "INSERT INTO main_images (page_id, content_url, width, height) VALUES (?, ?, ?, ?)",
                (
                    page_id,
                    article.main_image.content_url,
                    article.main_image.width,
                    article.main_image.height,
                ),
            )

    def _get_or_create_license(self, license_record: LicenseRecord) -> int:
        row = self._connection.execute(
            "SELECT license_id FROM licenses WHERE identifier = ? AND url = ?",
            (license_record.identifier, license_record.url),
        ).fetchone()
        if row is not None:
            return int(row[0])
        cursor = self._connection.execute(
            "INSERT INTO licenses (identifier, name, url) VALUES (?, ?, ?)",
            (license_record.identifier, license_record.name, license_record.url),
        )
        if cursor.lastrowid is None:
            raise RawRepositoryError("failed to allocate license_id")
        return cursor.lastrowid
