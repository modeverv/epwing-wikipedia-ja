"""Media deduplication by real content hash (TASK-O009, ARCHITECTURE.md 15.3).

TASK-O003's `select_media` already drops duplicate `source_url`s, but
that's only a proxy for 15.3's actual "duplicate hash" exclusion --
useful before any bytes exist, but blind to two different URLs (a
differently-sized thumbnail rendition, a mirrored copy) that turn out to
be the exact same file once downloaded. This module does the real
version, using TASK-O008's `compute_content_hash` on the downloaded
bytes: the first `MediaReference` seen for a given content hash is kept,
every later one pointing at byte-identical content is dropped.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from wikiepwing.model.article import MediaReference


@dataclass(frozen=True, slots=True)
class HashedMedia:
    """A `MediaReference` paired with the content hash of its downloaded bytes."""

    media: MediaReference
    content_hash: str


def deduplicate_media(entries: Sequence[HashedMedia]) -> tuple[MediaReference, ...]:
    """Return each entry's `MediaReference`, keeping only the first per content hash."""
    seen_hashes: set[str] = set()
    result: list[MediaReference] = []
    for entry in entries:
        if entry.content_hash in seen_hashes:
            continue
        seen_hashes.add(entry.content_hash)
        result.append(entry.media)
    return tuple(result)
