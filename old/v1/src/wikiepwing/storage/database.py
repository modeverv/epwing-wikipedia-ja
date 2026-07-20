"""Deterministic SQLite storage for raw MediaWiki records."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RawPage:
    page_id: int
    title: str
    namespace: int
    revision_id: int | None
    text: str
    redirect_target: str | None


class RawPageStore:
    """Small, transaction-batched SQLite adapter isolated from XML parsing."""

    def __init__(self, path: Path) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS raw_pages (
                page_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                namespace INTEGER NOT NULL,
                revision_id INTEGER,
                text TEXT NOT NULL,
                redirect_target TEXT
            );
            CREATE INDEX IF NOT EXISTS raw_pages_title ON raw_pages(title);
            CREATE TABLE IF NOT EXISTS build_diagnostics (
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL,
                detail TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stage_metadata (
                stage TEXT PRIMARY KEY, version INTEGER NOT NULL, status TEXT NOT NULL
            );
            """
        )
        self.connection.execute(
            "INSERT OR REPLACE INTO schema_metadata(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self.connection.commit()

    def insert_batch(self, pages: list[RawPage]) -> None:
        """Insert one batch; reruns accept only byte-for-byte identical page records."""
        with self.connection:
            for page in pages:
                row = (
                    page.page_id,
                    page.title,
                    page.namespace,
                    page.revision_id,
                    page.text,
                    page.redirect_target,
                )
                existing = self.connection.execute(
                    "SELECT page_id, title, namespace, revision_id, text, redirect_target "
                    "FROM raw_pages WHERE page_id = ?",
                    (page.page_id,),
                ).fetchone()
                if existing is None:
                    self.connection.execute("INSERT INTO raw_pages VALUES (?, ?, ?, ?, ?, ?)", row)
                elif tuple(existing) != row:
                    raise ValueError(f"conflicting duplicate page_id: {page.page_id}")

    def pages(self) -> Iterator[RawPage]:
        """Yield raw records in deterministic title order without materializing the dump."""
        rows = self.connection.execute(
            "SELECT page_id, title, namespace, revision_id, text, redirect_target "
            "FROM raw_pages ORDER BY title, page_id"
        )
        for row in rows:
            yield RawPage(*row)

    def close(self) -> None:
        self.connection.close()
