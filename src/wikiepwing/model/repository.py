"""Batch SQLite repository writer for model.sqlite3 (TASK-G012).

Mirrors `wikiepwing.ingest.repository.RawRepository`'s batch/prepared-statement/
foreign-key-ordered-replace pattern for the model database (TASK-F007's schema).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from wikiepwing.ingest.zstd_codec import compress
from wikiepwing.model.article import Article
from wikiepwing.model.blocks import (
    Block,
    InfoboxBlock,
    OrderedListBlock,
    QuoteBlock,
    ReferencesBlock,
    TableBlock,
    UnorderedListBlock,
)
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import Inline, InternalLinkInline


class ModelRepositoryError(RuntimeError):
    """Raised when a model repository write cannot proceed safely."""


@dataclass(frozen=True, slots=True)
class ArticleWrite:
    """One fully computed article waiting for a bulk repository write."""

    article: Article
    canonical_json: bytes
    logical_hash: str
    normalize_status: str
    canonical_json_zstd: bytes | None = None


class ModelRepository:
    """Prepared-statement writer for one model.sqlite3 connection."""

    def __init__(self, connection: sqlite3.Connection, *, zstd_level: int = 6) -> None:
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise ModelRepositoryError("connection must have PRAGMA foreign_keys enabled")
        self._connection = connection
        self._zstd_level = zstd_level
        # The full model build is append-heavy and the user explicitly permits a
        # large memory footprint. Keep hot B-tree pages and temporary sort data in RAM.
        self._connection.execute("PRAGMA cache_size = -4194304")
        self._connection.execute("PRAGMA temp_store = MEMORY")
        self._connection.execute("PRAGMA mmap_size = 8589934592")

    def defer_link_target_index(self) -> bool:
        """Drop the costly secondary link index for a fresh bulk build."""
        article_count = self._connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        index_exists = self._connection.execute(
            "SELECT 1 FROM sqlite_schema WHERE type = 'index' AND name = 'links_target'"
        ).fetchone()
        if article_count:
            if index_exists is None:
                # A killed bulk build intentionally leaves this index deferred.
                # A forced full rerun replaces every accepted article and restores it.
                return True
            return False
        if index_exists is None:
            raise ModelRepositoryError("fresh model is missing required links_target index")
        self._connection.execute("DROP INDEX links_target")
        return True

    def restore_link_target_index(self) -> None:
        """Build the deferred secondary index once, after all link rows exist."""
        self._connection.execute("CREATE INDEX links_target ON links(target_page_id)")
        self._connection.commit()

    def deferred_bulk_article_ids(self) -> set[int]:
        """Return existing article ids only for an interrupted deferred-index build."""
        index_exists = self._connection.execute(
            "SELECT 1 FROM sqlite_schema WHERE type = 'index' AND name = 'links_target'"
        ).fetchone()
        if index_exists is not None:
            return set()
        return {
            int(row["page_id"])
            for row in self._connection.execute("SELECT page_id FROM articles ORDER BY page_id")
        }

    def current_metrics(self) -> tuple[int, int, int, dict[str, int]]:
        """Return metrics already present in an interrupted model database."""
        status_rows = self._connection.execute(
            "SELECT normalize_status, COUNT(*) AS count FROM articles GROUP BY normalize_status"
        ).fetchall()
        written = 0
        rejected = 0
        for row in status_rows:
            count = int(row["count"])
            if row["normalize_status"] == "rejected":
                rejected += count
            else:
                written += count
        severity_rows = self._connection.execute(
            "SELECT severity, COUNT(*) AS count FROM diagnostics GROUP BY severity"
        ).fetchall()
        severity_counts = {str(row["severity"]): int(row["count"]) for row in severity_rows}
        return written + rejected, written, rejected, severity_counts

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

    def write_article(
        self,
        article: Article,
        *,
        canonical_json: bytes,
        logical_hash: str,
        normalize_status: str,
    ) -> None:
        """Upsert one article and replace its child rows (links, media, diagnostics)."""
        article_blob = compress(canonical_json, level=self._zstd_level)
        self._connection.execute(
            """
            INSERT INTO articles (
                page_id, revision_id, title, normalized_title, source_url,
                source_date_modified, abstract, article_json_zstd, article_logical_hash,
                normalize_status, block_count, diagnostic_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(page_id) DO UPDATE SET
                revision_id = excluded.revision_id,
                title = excluded.title,
                normalized_title = excluded.normalized_title,
                source_url = excluded.source_url,
                source_date_modified = excluded.source_date_modified,
                abstract = excluded.abstract,
                article_json_zstd = excluded.article_json_zstd,
                article_logical_hash = excluded.article_logical_hash,
                normalize_status = excluded.normalize_status,
                block_count = excluded.block_count,
                diagnostic_count = excluded.diagnostic_count
            """,
            (
                article.page_id,
                article.revision_id,
                article.title,
                article.normalized_title,
                article.source_url,
                article.source_date_modified.isoformat(),
                article.abstract,
                article_blob,
                logical_hash,
                normalize_status,
                len(article.blocks),
                len(article.diagnostics),
            ),
        )
        self._replace_children(article)

    def write_articles(self, writes: list[ArticleWrite]) -> None:
        """Replace many articles and all child rows with table-sized bulk operations."""
        if not writes:
            return
        page_ids = [(write.article.page_id,) for write in writes]
        self._connection.executemany("DELETE FROM links WHERE source_page_id = ?", page_ids)
        self._connection.executemany("DELETE FROM media_references WHERE page_id = ?", page_ids)
        self._connection.executemany("DELETE FROM diagnostics WHERE page_id = ?", page_ids)

        self._connection.executemany(
            """
            INSERT INTO articles (
                page_id, revision_id, title, normalized_title, source_url,
                source_date_modified, abstract, article_json_zstd, article_logical_hash,
                normalize_status, block_count, diagnostic_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(page_id) DO UPDATE SET
                revision_id = excluded.revision_id,
                title = excluded.title,
                normalized_title = excluded.normalized_title,
                source_url = excluded.source_url,
                source_date_modified = excluded.source_date_modified,
                abstract = excluded.abstract,
                article_json_zstd = excluded.article_json_zstd,
                article_logical_hash = excluded.article_logical_hash,
                normalize_status = excluded.normalize_status,
                block_count = excluded.block_count,
                diagnostic_count = excluded.diagnostic_count
            """,
            [self._article_row(write) for write in writes],
        )

        link_rows: list[tuple[object, ...]] = []
        media_rows: list[tuple[object, ...]] = []
        diagnostic_rows: list[tuple[object, ...]] = []
        for write in writes:
            article = write.article
            link_rows.extend(
                (
                    article.page_id,
                    ordinal,
                    link.target_page_id,
                    link.target_title,
                    link.target_fragment,
                    link.resolution,
                )
                for ordinal, link in enumerate(_extract_links(article.blocks))
            )
            media_rows.extend(
                (
                    article.page_id,
                    ordinal,
                    media.media_id,
                    media.source_url,
                    media.source_name,
                    media.alt_text,
                    media.caption,
                    media.role,
                    media.source_width,
                    media.source_height,
                )
                for ordinal, media in enumerate(article.media)
            )
            diagnostic_rows.extend(self._diagnostic_row(item) for item in article.diagnostics)

        self._connection.executemany(
            """
            INSERT INTO links (
                source_page_id, ordinal, target_page_id, target_title,
                target_fragment, resolution
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            link_rows,
        )
        self._connection.executemany(
            """
            INSERT INTO media_references (
                page_id, ordinal, media_id, source_url, source_name, alt_text,
                caption, role, source_width, source_height
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            media_rows,
        )
        self._connection.executemany(
            """
            INSERT INTO diagnostics (
                code, severity, stage, page_id, title, message, source_path,
                source_excerpt, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            diagnostic_rows,
        )

    def _article_row(self, write: ArticleWrite) -> tuple[object, ...]:
        article = write.article
        return (
            article.page_id,
            article.revision_id,
            article.title,
            article.normalized_title,
            article.source_url,
            article.source_date_modified.isoformat(),
            article.abstract,
            (
                write.canonical_json_zstd
                if write.canonical_json_zstd is not None
                else compress(write.canonical_json, level=self._zstd_level)
            ),
            write.logical_hash,
            write.normalize_status,
            len(article.blocks),
            len(article.diagnostics),
        )

    @staticmethod
    def _diagnostic_row(diagnostic: Diagnostic) -> tuple[object, ...]:
        return (
            diagnostic.code,
            diagnostic.severity,
            diagnostic.stage,
            diagnostic.page_id,
            diagnostic.title,
            diagnostic.message,
            diagnostic.source_path,
            diagnostic.source_excerpt,
            json.dumps(diagnostic.details, ensure_ascii=False, sort_keys=True),
        )

    def _replace_children(self, article: Article) -> None:
        page_id = article.page_id
        self._connection.execute("DELETE FROM links WHERE source_page_id = ?", (page_id,))
        self._connection.execute("DELETE FROM media_references WHERE page_id = ?", (page_id,))
        self._connection.execute("DELETE FROM diagnostics WHERE page_id = ?", (page_id,))

        links = _extract_links(article.blocks)
        self._connection.executemany(
            """
                INSERT INTO links (
                    source_page_id, ordinal, target_page_id, target_title,
                    target_fragment, resolution
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
            [
                (
                    page_id,
                    ordinal,
                    link.target_page_id,
                    link.target_title,
                    link.target_fragment,
                    link.resolution,
                )
                for ordinal, link in enumerate(links)
            ],
        )

        for ordinal, media in enumerate(article.media):
            self._connection.execute(
                """
                INSERT INTO media_references (
                    page_id, ordinal, media_id, source_url, source_name, alt_text,
                    caption, role, source_width, source_height
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    page_id,
                    ordinal,
                    media.media_id,
                    media.source_url,
                    media.source_name,
                    media.alt_text,
                    media.caption,
                    media.role,
                    media.source_width,
                    media.source_height,
                ),
            )

        for diagnostic in article.diagnostics:
            self._write_diagnostic(diagnostic)

    def _write_diagnostic(self, diagnostic: Diagnostic) -> None:
        self._connection.execute(
            """
            INSERT INTO diagnostics (
                code, severity, stage, page_id, title, message, source_path,
                source_excerpt, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                diagnostic.code,
                diagnostic.severity,
                diagnostic.stage,
                diagnostic.page_id,
                diagnostic.title,
                diagnostic.message,
                diagnostic.source_path,
                diagnostic.source_excerpt,
                json.dumps(diagnostic.details, ensure_ascii=False, sort_keys=True),
            ),
        )


def _extract_links(blocks: tuple[Block, ...]) -> tuple[InternalLinkInline, ...]:
    links: list[InternalLinkInline] = []
    for block in blocks:
        links.extend(_extract_links_from_block(block))
    return tuple(links)


def _extract_links_from_block(block: Block) -> list[InternalLinkInline]:
    links: list[InternalLinkInline] = []
    inlines = getattr(block, "inlines", None)
    if inlines is not None:
        links.extend(_extract_links_from_inlines(inlines))
    caption = getattr(block, "caption", None)
    if caption is not None:
        links.extend(_extract_links_from_inlines(caption))
    if isinstance(block, ReferencesBlock):
        for item in block.items:
            links.extend(_extract_links_from_inlines(item))
    for child in _child_blocks(block):
        links.extend(_extract_links_from_block(child))
    return links


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


def _extract_links_from_inlines(inlines: tuple[Inline, ...]) -> list[InternalLinkInline]:
    links: list[InternalLinkInline] = []
    for inline in inlines:
        if isinstance(inline, InternalLinkInline):
            links.append(inline)
            links.extend(_extract_links_from_inlines(inline.label))
        else:
            nested = getattr(inline, "inlines", None) or getattr(inline, "label", None)
            if nested is not None:
                links.extend(_extract_links_from_inlines(nested))
    return links
