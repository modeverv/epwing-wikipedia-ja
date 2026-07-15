"""Media role classification (TASK-O002, ARCHITECTURE.md 15.3).

TASK-O001 always extracts a `MediaReference` with `role="unknown"`; this
module resolves it into 15.3's actual priority tiers using what little
context is available at normalize time: whether the image was found
inside an infobox (TASK-K008's `RawInfobox.image_srcs`), whether it's the
lead figure, and whether its dimensions look like one of 15.3's excluded
"16pxなどのicon" candidates. `role="main"` (set directly by
`normalize/orchestrate.py`'s `_read_media` from the Wikimedia Enterprise
Snapshot's own main-image field) is never overridden here -- it is
already authoritative, not something inferred from DOM context.

Deciding which images actually make it into the final `Article.media`
(deduplication, exclusion of decorative/tracking images) is TASK-O003's
selection policy; this module only assigns a role.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import replace

from wikiepwing.model.article import MediaReference, MediaRole

_ICON_MAX_DIMENSION = 20


def classify_media_role(
    media: MediaReference,
    *,
    infobox_source_urls: Collection[str] = (),
    is_lead: bool = False,
) -> MediaRole:
    """Return the role `media` should have, given its normalize-time context."""
    if media.role == "main":
        return "main"
    if _is_icon_sized(media):
        return "icon"
    if media.source_url in infobox_source_urls:
        return "infobox"
    if is_lead:
        return "lead"
    return "body"


def with_classified_role(
    media: MediaReference,
    *,
    infobox_source_urls: Collection[str] = (),
    is_lead: bool = False,
) -> MediaReference:
    """Return `media` with its role resolved by `classify_media_role`."""
    role = classify_media_role(media, infobox_source_urls=infobox_source_urls, is_lead=is_lead)
    return replace(media, role=role)


def _is_icon_sized(media: MediaReference) -> bool:
    return (
        media.source_width is not None
        and media.source_height is not None
        and media.source_width <= _ICON_MAX_DIMENSION
        and media.source_height <= _ICON_MAX_DIMENSION
    )
