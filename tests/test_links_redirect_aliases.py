from __future__ import annotations

import sqlite3
from pathlib import Path

from wikiepwing.ingest.database import connect_raw_database, initialize_raw_database
from wikiepwing.links.redirect_aliases import extract_redirect_aliases
from wikiepwing.model.article import Alias

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "raw"


def _insert_article(connection: sqlite3.Connection, *, page_id: int) -> None:
    connection.execute(
        """
        INSERT INTO articles (
            page_id, revision_id, title, normalized_title, namespace_id, url,
            date_modified, source_hash, source_sequence, ingest_status
        ) VALUES (?, 1, 'Emacs', 'Emacs', 0, 'https://ja.wikipedia.org/wiki/Emacs',
                  '2026-06-01T00:00:00Z', ?, 0, 'accepted')
        """,
        (page_id, "a" * 64),
    )


def _insert_redirect(
    connection: sqlite3.Connection, *, target_page_id: int, redirect_title: str, ordinal: int
) -> None:
    connection.execute(
        """
        INSERT INTO redirects (target_page_id, redirect_title, normalized_redirect_title, ordinal)
        VALUES (?, ?, ?, ?)
        """,
        (target_page_id, redirect_title, redirect_title, ordinal),
    )


def test_extract_redirect_aliases_returns_ordinal_order(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        _insert_article(connection, page_id=1)
        _insert_redirect(connection, target_page_id=1, redirect_title="GNU", ordinal=1)
        _insert_redirect(connection, target_page_id=1, redirect_title="GNU Emacs", ordinal=0)

        aliases = extract_redirect_aliases(connection, 1)

        assert aliases == (
            Alias(title="GNU Emacs", source="redirect", confidence=1.0),
            Alias(title="GNU", source="redirect", confidence=1.0),
        )


def test_extract_redirect_aliases_returns_empty_when_none(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    with connect_raw_database(database) as connection:
        _insert_article(connection, page_id=1)

        aliases = extract_redirect_aliases(connection, 1)

        assert aliases == ()
