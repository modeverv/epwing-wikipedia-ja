"""Redirect-sourced alias extraction (TASK-H004, ARCHITECTURE.md 13.3 alias source).

Redirects are the first alias candidate ARCHITECTURE.md 13.3 lists; since they
are curated wiki data (not a heuristic guess), they get a fixed confidence of
1.0. Other alias sources (title/normalized title variant/HTML display title/
lead bold/Wikidata) are separate, later work.
"""

from __future__ import annotations

import sqlite3

from wikiepwing.model.article import Alias

_REDIRECT_ALIAS_CONFIDENCE = 1.0


def extract_redirect_aliases(connection: sqlite3.Connection, page_id: int) -> tuple[Alias, ...]:
    """Return the redirect-sourced aliases for `page_id`, in raw.sqlite3 ordinal order."""
    rows = connection.execute(
        "SELECT redirect_title FROM redirects WHERE target_page_id = ? ORDER BY ordinal",
        (page_id,),
    ).fetchall()
    return tuple(
        Alias(title=row["redirect_title"], source="redirect", confidence=_REDIRECT_ALIAS_CONFIDENCE)
        for row in rows
    )
