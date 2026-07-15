"""Body media extraction and classification (TASK-O012, wiring TASK-O001-O002).

Walks the DOM tree `convert_document` builds Blocks from to find every
`<img>`/`<figure>` element (TASK-O001), classifies each one's role
(TASK-O002) using infobox image `src`s found via TASK-K008's infobox
parser and "the first non-icon, non-infobox image in document order is
the lead figure" (ARCHITECTURE.md 15.3's "lead figure" tier). This is a
single, separate walk over the raw DOM rather than a new return channel
threaded through `convert_block`/`convert_inline_nodes` -- much less
invasive, and "what media does this article reference" is normalize's
own concern, independent of how the Block tree renders.

`classify_body_media` deliberately stops short of TASK-O003's selection
policy (dedup/ordering/icon exclusion): the caller combines this with
the Snapshot's own main-image `MediaReference` (already `role="main"`)
before running `select_media` once over the combined list, so a main
image and a body image that happen to share a `source_url` dedup
correctly against each other too.
"""

from __future__ import annotations

from wikiepwing.model.article import MediaReference
from wikiepwing.normalize.html_parser import ElementNode, Node
from wikiepwing.normalize.infobox import is_infobox
from wikiepwing.normalize.infobox_fields import parse_infobox_dom
from wikiepwing.normalize.media_node import (
    is_figure_with_image,
    is_image_node,
    parse_figure_media,
    parse_image_node,
)
from wikiepwing.normalize.media_role import with_classified_role


def classify_body_media(nodes: tuple[Node, ...]) -> tuple[MediaReference, ...]:
    """Extract and role-classify every image reference found in `nodes`."""
    infobox_source_urls = _collect_infobox_image_srcs(nodes)
    raw_media = _collect_raw_media(nodes)

    lead_claimed = False
    classified: list[MediaReference] = []
    for media in raw_media:
        result = with_classified_role(
            media,
            infobox_source_urls=infobox_source_urls,
            is_lead=not lead_claimed,
        )
        if result.role == "lead":
            lead_claimed = True
        classified.append(result)
    return tuple(classified)


def _collect_raw_media(nodes: tuple[Node, ...]) -> list[MediaReference]:
    found: list[MediaReference] = []

    def visit(node: Node) -> None:
        if not isinstance(node, ElementNode):
            return
        if is_figure_with_image(node):
            media = parse_figure_media(node)
            if media is not None:
                found.append(media)
            return
        if is_image_node(node):
            media = parse_image_node(node)
            if media is not None:
                found.append(media)
            return
        for child in node.children:
            visit(child)

    for node in nodes:
        visit(node)
    return found


def _collect_infobox_image_srcs(nodes: tuple[Node, ...]) -> frozenset[str]:
    srcs: set[str] = set()

    def visit(node: Node) -> None:
        if not isinstance(node, ElementNode):
            return
        if is_infobox(node):
            raw_infobox, _diagnostics = parse_infobox_dom(node)
            srcs.update(raw_infobox.image_srcs)
            return
        for child in node.children:
            visit(child)

    for node in nodes:
        visit(node)
    return frozenset(srcs)
