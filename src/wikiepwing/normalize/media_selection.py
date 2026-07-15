"""Media selection policy (TASK-O003, ARCHITECTURE.md 15.3).

Takes TASK-O002's role-classified `MediaReference`s and produces the
final ordered list for `Article.media`: drop 15.3's excluded
"16pxなどのicon" candidates, drop duplicates, and order the rest by
15.3's priority (主画像 > Infobox主要画像 > lead figure > 本文画像).
Real content-hash deduplication needs the file bytes, which aren't
downloaded until TASK-O004 onward; `source_url` is this stage's
practical stand-in for "duplicate hash" -- the same URL is certainly the
same file, even before that file has been fetched. A stable sort
preserves each role tier's original (DOM) order, matching 15.3's
"本文先頭の意味ある画像" before "追加本文画像" split within the same
`body` tier.
"""

from __future__ import annotations

from collections.abc import Sequence

from wikiepwing.model.article import MediaReference, MediaRole

_ROLE_PRIORITY: dict[MediaRole, int] = {
    "main": 0,
    "infobox": 1,
    "lead": 2,
    "body": 3,
    "unknown": 4,
    "icon": 5,
}


def select_media(media_list: Sequence[MediaReference]) -> tuple[MediaReference, ...]:
    """Return `media_list` filtered of icons/duplicates and ordered by role priority."""
    seen_urls: set[str] = set()
    candidates: list[MediaReference] = []
    for media in media_list:
        if media.role == "icon":
            continue
        if media.source_url in seen_urls:
            continue
        seen_urls.add(media.source_url)
        candidates.append(media)

    return tuple(sorted(candidates, key=lambda media: _ROLE_PRIORITY[media.role]))
