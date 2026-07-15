"""Media reference extraction (TASK-O001, ARCHITECTURE.md 15.1/15.2).

15.1: "Normalizationは画像参照だけを保存します。ダウンロードしません。" --
this module only reads `<img>` (and `<figure>`+`<figcaption>`) attributes
into a `MediaReference`; it never fetches the referenced URL. `role`
always comes back `"unknown"` here -- classifying it into 15.2's
`main`/`infobox`/`lead`/`body`/`icon` set is TASK-O002's job, which (like
TASK-O010's attribution model) takes this module's output as its input.

`media_id` reuses `source_url` itself, matching the existing precedent in
`normalize/orchestrate.py`'s `_read_media` (which sets
`media_id=row["content_url"]` for the Wikimedia Enterprise Snapshot's
main-image metadata) rather than inventing a second identifier scheme.
"""

from __future__ import annotations

from urllib.parse import unquote, urlsplit

from wikiepwing.model.article import MediaReference
from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode


def is_image_node(node: Node) -> bool:
    """Return whether `node` is an `<img>` element."""
    return isinstance(node, ElementNode) and node.tag == "img"


def parse_image_node(node: ElementNode, *, caption: str | None = None) -> MediaReference | None:
    """Extract a `MediaReference` from an `<img>` element, or None if it has no `src`."""
    if node.tag != "img":
        raise ValueError(f"not an img element: <{node.tag}>")
    source_url = _attribute(node, "src")
    if not source_url:
        return None
    return MediaReference(
        media_id=source_url,
        source_url=source_url,
        source_name=_source_name(source_url),
        alt_text=_attribute(node, "alt") or None,
        caption=caption,
        role="unknown",
        source_width=_positive_int(_attribute(node, "width")),
        source_height=_positive_int(_attribute(node, "height")),
    )


def is_figure_with_image(node: Node) -> bool:
    """Return whether `node` is a `<figure>` element containing an `<img>`."""
    return isinstance(node, ElementNode) and node.tag == "figure" and _find_image(node) is not None


def parse_figure_media(node: ElementNode) -> MediaReference | None:
    """Extract a `MediaReference` from a `<figure>`, using `<figcaption>` text as its caption."""
    if node.tag != "figure":
        raise ValueError(f"not a figure element: <{node.tag}>")
    image = _find_image(node)
    if image is None:
        return None
    return parse_image_node(image, caption=_find_caption(node))


def _find_image(node: ElementNode) -> ElementNode | None:
    for child in node.children:
        if isinstance(child, ElementNode):
            if child.tag == "img":
                return child
            found = _find_image(child)
            if found is not None:
                return found
    return None


def _find_caption(node: ElementNode) -> str | None:
    for child in node.children:
        if isinstance(child, ElementNode) and child.tag == "figcaption":
            text = _flatten_text(child)
            return text if text else None
    return None


def _flatten_text(node: ElementNode) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, TextNode):
            parts.append(child.text)
        elif isinstance(child, ElementNode):
            parts.append(_flatten_text(child))
    return "".join(parts).strip()


def _attribute(node: ElementNode, name: str) -> str | None:
    for attribute_name, value in node.attributes:
        if attribute_name == name:
            return value
    return None


def _source_name(source_url: str) -> str | None:
    path = urlsplit(source_url).path
    filename = path.rsplit("/", 1)[-1]
    return unquote(filename) if filename else None


def _positive_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None
