from __future__ import annotations

import sqlite3
from pathlib import Path

from wikiepwing.ingest.database import connect_raw_database, initialize_raw_database
from wikiepwing.links.resolver import resolve_internal_link
from wikiepwing.links.url_parser import ParsedInternalUrl

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "raw"


def _insert_article(
    connection: sqlite3.Connection, *, page_id: int, title: str, normalized_title: str
) -> None:
    connection.execute(
        """
        INSERT INTO articles (
            page_id, revision_id, title, normalized_title, namespace_id, url,
            date_modified, source_hash, source_sequence, ingest_status
        ) VALUES (?, 1, ?, ?, 0, 'https://ja.wikipedia.org/wiki/X', '2026-06-01T00:00:00Z',
                  ?, 0, 'accepted')
        """,
        (page_id, title, normalized_title, "a" * 64),
    )


def _insert_redirect(
    connection: sqlite3.Connection, *, target_page_id: int, redirect_title: str, normalized: str
) -> None:
    connection.execute(
        """
        INSERT INTO redirects (target_page_id, redirect_title, normalized_redirect_title, ordinal)
        VALUES (?, ?, ?, 0)
        """,
        (target_page_id, redirect_title, normalized),
    )


def test_resolves_direct_article_match(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        _insert_article(connection, page_id=1, title="Emacs", normalized_title="Emacs")

        parsed = ParsedInternalUrl(namespace=None, title="Emacs", fragment=None)
        resolved = resolve_internal_link(parsed, connection)

        assert resolved.resolution == "resolved"
        assert resolved.target_page_id == 1
        assert resolved.target_normalized_title == "Emacs"


def test_resolves_via_redirect_when_following(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        _insert_article(connection, page_id=1, title="Emacs", normalized_title="Emacs")
        _insert_redirect(
            connection, target_page_id=1, redirect_title="GNU Emacs", normalized="GNU Emacs"
        )

        parsed = ParsedInternalUrl(namespace=None, title="GNU Emacs", fragment=None)
        resolved = resolve_internal_link(parsed, connection, follow_redirects=True)

        assert resolved.resolution == "resolved"
        assert resolved.target_page_id == 1


def test_redirect_not_followed_when_disabled(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        _insert_article(connection, page_id=1, title="Emacs", normalized_title="Emacs")
        _insert_redirect(
            connection, target_page_id=1, redirect_title="GNU Emacs", normalized="GNU Emacs"
        )

        parsed = ParsedInternalUrl(namespace=None, title="GNU Emacs", fragment=None)
        resolved = resolve_internal_link(parsed, connection, follow_redirects=False)

        assert resolved.resolution == "missing"
        assert resolved.target_page_id is None


def test_missing_when_no_match(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        parsed = ParsedInternalUrl(namespace=None, title="Nonexistent Page", fragment=None)
        resolved = resolve_internal_link(parsed, connection)

        assert resolved.resolution == "missing"
        assert resolved.target_page_id is None


def test_namespaced_link_is_externalized(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        _insert_article(
            connection, page_id=1, title="Text editors", normalized_title="Text editors"
        )

        parsed = ParsedInternalUrl(namespace="Category", title="Text editors", fragment=None)
        resolved = resolve_internal_link(parsed, connection)

        assert resolved.resolution == "externalized"
        assert resolved.target_page_id is None


def test_preserves_fragment_across_resolution(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        _insert_article(connection, page_id=1, title="Emacs", normalized_title="Emacs")

        parsed = ParsedInternalUrl(namespace=None, title="Emacs", fragment="History")
        resolved = resolve_internal_link(parsed, connection)

        assert resolved.target_fragment == "History"
