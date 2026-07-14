"""Batch SQLite repository writer for model.sqlite3 (TASK-G012).

Mirrors `wikiepwing.ingest.repository.RawRepository`'s batch/prepared-statement/
foreign-key-ordered-replace pattern for the model database (TASK-F007's schema).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

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


class ModelRepository:
    """Prepared-statement writer for one model.sqlite3 connection."""

    def __init__(self, connection: sqlite3.Connection, *, zstd_level: int = 6) -> None:
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise ModelRepositoryError("connection must have PRAGMA foreign_keys enabled")
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

    def _replace_children(self, article: Article) -> None:
        page_id = article.page_id
        self._connection.execute("DELETE FROM links WHERE source_page_id = ?", (page_id,))
        self._connection.execute("DELETE FROM media_references WHERE page_id = ?", (page_id,))
        self._connection.execute("DELETE FROM diagnostics WHERE page_id = ?", (page_id,))

        for ordinal, link in enumerate(_extract_links(article.blocks)):
            self._connection.execute(
                """
                INSERT INTO links (
                    source_page_id, ordinal, target_page_id, target_title,
                    target_fragment, resolution
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    page_id,
                    ordinal,
                    link.target_page_id,
                    link.target_title,
                    link.target_fragment,
                    link.resolution,
                ),
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
