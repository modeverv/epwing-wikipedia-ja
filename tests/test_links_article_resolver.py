from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from wikiepwing.ingest.database import connect_raw_database, initialize_raw_database
from wikiepwing.links.article_resolver import resolve_article_links
from wikiepwing.model.article import Article
from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.inline import ExternalLinkInline, InternalLinkInline, TextInline

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "raw"


def _insert_article(
    connection: sqlite3.Connection, *, page_id: int, title: str, normalized_title: str
) -> None:
    connection.execute(
        """
        INSERT INTO articles (
            page_id, revision_id, title, normalized_title, namespace_id, url,
            date_modified, source_hash, source_sequence, ingest_status
        ) VALUES (?, 1, ?, ?, 0, 'https://ja.wikipedia.org/wiki/X',
                  '2026-06-01T00:00:00Z', ?, 0, 'accepted')
        """,
        (page_id, title, normalized_title, "a" * 64),
    )


def _article(*inlines: object) -> Article:
    return Article(
        page_id=10,
        revision_id=1,
        title="Source",
        normalized_title="Source",
        source_url="https://ja.wikipedia.org/wiki/Source",
        source_date_modified=datetime(2026, 6, 1, tzinfo=UTC),
        abstract=None,
        blocks=(ParagraphBlock(inlines=inlines),),  # type: ignore[arg-type]
        aliases=(),
        categories=(),
        media=(),
        diagnostics=(),
        source_license_ids=(),
    )


def test_resolves_direct_redirect_missing_and_same_project_absolute_links(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        _insert_article(connection, page_id=1, title="日本の歴史", normalized_title="日本の歴史")
        connection.execute(
            "INSERT INTO redirects "
            "(target_page_id, redirect_title, normalized_redirect_title, ordinal) "
            "VALUES (1, '日本史', '日本史', 0)"
        )
        source = _article(
            InternalLinkInline(
                label=(TextInline(value="歴史"),),
                target_title="日本の歴史",
                target_normalized_title="日本の歴史",
                target_fragment="概要",
                target_page_id=None,
                resolution="missing",
            ),
            InternalLinkInline(
                label=(TextInline(value="日本史"),),
                target_title="日本史",
                target_normalized_title="日本史",
                target_fragment=None,
                target_page_id=None,
                resolution="missing",
            ),
            InternalLinkInline(
                label=(TextInline(value="不存在"),),
                target_title="不存在",
                target_normalized_title="不存在",
                target_fragment=None,
                target_page_id=None,
                resolution="missing",
            ),
            ExternalLinkInline(
                label=(TextInline(value="絶対URL"),),
                url="https://ja.wikipedia.org/wiki/日本の歴史",
            ),
        )

        resolved = resolve_article_links(
            source, connection, project_base_urls=("https://ja.wikipedia.org",)
        )

    links = resolved.blocks[0].inlines  # type: ignore[union-attr]
    assert [(link.resolution, link.target_page_id) for link in links] == [  # type: ignore[union-attr]
        ("resolved", 1),
        ("resolved", 1),
        ("missing", None),
        ("resolved", 1),
    ]
    assert links[0].target_fragment == "概要"  # type: ignore[union-attr]


def test_preserves_externalized_namespace_and_external_site(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        namespace = InternalLinkInline(
            label=(TextInline(value="カテゴリ"),),
            target_title="日本",
            target_normalized_title="日本",
            target_fragment=None,
            target_page_id=None,
            resolution="externalized",
        )
        external = ExternalLinkInline(
            label=(TextInline(value="source"),), url="https://example.org/source"
        )

        resolved = resolve_article_links(
            _article(namespace, external),
            connection,
            project_base_urls=("https://ja.wikipedia.org",),
        )

    assert resolved.blocks[0].inlines == (namespace, external)  # type: ignore[union-attr]


def test_reuses_resolution_cache_and_preserves_each_fragment(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        _insert_article(connection, page_id=1, title="日本", normalized_title="日本")
        cache = {}
        first = resolve_article_links(
            _article(
                InternalLinkInline(
                    label=(TextInline(value="概要"),),
                    target_title="日本",
                    target_normalized_title="日本",
                    target_fragment="概要",
                    target_page_id=None,
                    resolution="missing",
                )
            ),
            connection,
            project_base_urls=("https://ja.wikipedia.org",),
            resolution_cache=cache,
        )

        traced_statements: list[str] = []
        connection.set_trace_callback(traced_statements.append)
        second = resolve_article_links(
            _article(
                InternalLinkInline(
                    label=(TextInline(value="歴史"),),
                    target_title="日本",
                    target_normalized_title="日本",
                    target_fragment="歴史",
                    target_page_id=None,
                    resolution="missing",
                )
            ),
            connection,
            project_base_urls=("https://ja.wikipedia.org",),
            resolution_cache=cache,
        )
        connection.set_trace_callback(None)

    first_link = first.blocks[0].inlines[0]  # type: ignore[union-attr]
    second_link = second.blocks[0].inlines[0]  # type: ignore[union-attr]
    assert first_link.target_fragment == "概要"  # type: ignore[union-attr]
    assert second_link.target_fragment == "歴史"  # type: ignore[union-attr]
    assert second_link.target_page_id == 1  # type: ignore[union-attr]
    assert traced_statements == []
