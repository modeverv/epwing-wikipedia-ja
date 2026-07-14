"""Internal link target resolution (TASK-H002, ARCHITECTURE.md 12.5 steps 5-7).

Resolves a `ParsedInternalUrl` (TASK-H001) against raw.sqlite3's `articles`/
`redirects` tables to decide an `InternalLinkInline.resolution` value. Links
outside this project's initial single-namespace scope (`Category:`, etc. --
`[source] namespace` is 0 only) are treated as `externalized` regardless of
whether a matching page happens to exist, since those namespaces are never
ingested in the first place. EPWING entry ID conversion is a later epic.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Literal

from wikiepwing.ingest.repository import normalize_title
from wikiepwing.links.url_parser import ParsedInternalUrl

Resolution = Literal["resolved", "missing", "externalized"]


@dataclass(frozen=True, slots=True)
class ResolvedLink:
    """The outcome of resolving one internal link against raw.sqlite3."""

    target_title: str
    target_normalized_title: str
    target_page_id: int | None
    target_fragment: str | None
    resolution: Resolution


def resolve_internal_link(
    parsed: ParsedInternalUrl,
    connection: sqlite3.Connection,
    *,
    follow_redirects: bool = True,
) -> ResolvedLink:
    """Resolve one parsed internal link URL to a page ID (or a non-resolved state)."""
    normalized = normalize_title(parsed.title)

    if parsed.namespace is not None:
        return ResolvedLink(
            target_title=parsed.title,
            target_normalized_title=normalized,
            target_page_id=None,
            target_fragment=parsed.fragment,
            resolution="externalized",
        )

    row = connection.execute(
        "SELECT page_id FROM articles WHERE normalized_title = ? AND ingest_status = 'accepted'",
        (normalized,),
    ).fetchone()
    if row is not None:
        return ResolvedLink(
            target_title=parsed.title,
            target_normalized_title=normalized,
            target_page_id=row[0],
            target_fragment=parsed.fragment,
            resolution="resolved",
        )

    if follow_redirects:
        redirect_row = connection.execute(
            "SELECT target_page_id FROM redirects WHERE normalized_redirect_title = ?",
            (normalized,),
        ).fetchone()
        if redirect_row is not None:
            return ResolvedLink(
                target_title=parsed.title,
                target_normalized_title=normalized,
                target_page_id=redirect_row[0],
                target_fragment=parsed.fragment,
                resolution="resolved",
            )

    return ResolvedLink(
        target_title=parsed.title,
        target_normalized_title=normalized,
        target_page_id=None,
        target_fragment=parsed.fragment,
        resolution="missing",
    )
