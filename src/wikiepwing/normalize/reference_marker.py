"""Reference marker parser (TASK-L001, ARCHITECTURE.md 12.2 "N100 Convert references").

MediaWiki's Cite extension renders an inline footnote marker as
`<sup id="cite_ref-..." class="reference"><a href="#cite_note-...">[1]</a>
</sup>` -- no algorithm for this is specified elsewhere, so this module
relies on that stable, well-known convention. EPWING plain text cannot
carry a hyperlink, so the marker's visible label (e.g. "[1]") is what
`wikiepwing.normalize.paragraphs.convert_inline_nodes`'s existing
transparent-wrapper fallback already recovers by recursing into `<sup>`/
`<a>`; what that fallback does *not* recover is the fragment id the
marker points to (`cite_note-...`), which TASK-L002 needs to match each
inline marker to its reference-list entry. This module extracts both.
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode, has_class

_MARKER_TAG = "sup"
_MARKER_CLASS = "reference"


@dataclass(frozen=True, slots=True)
class ReferenceMarker:
    """One inline footnote marker's visible label and target fragment id."""

    label: str
    target_id: str | None


def is_reference_marker(node: Node) -> bool:
    """Return whether `node` is a `<sup class="reference">` footnote marker."""
    return (
        isinstance(node, ElementNode) and node.tag == _MARKER_TAG and has_class(node, _MARKER_CLASS)
    )


def parse_reference_marker(node: ElementNode) -> ReferenceMarker:
    """Parse one reference marker element into its label and target fragment id."""
    if not (node.tag == _MARKER_TAG and has_class(node, _MARKER_CLASS)):
        raise ValueError(f"not a reference marker element: <{node.tag}>")
    return ReferenceMarker(label=_flatten_text(node), target_id=_find_fragment_target(node))


def _find_fragment_target(node: ElementNode) -> str | None:
    for child in node.children:
        if isinstance(child, ElementNode):
            if child.tag == "a":
                href = _attribute(child, "href")
                if href and href.startswith("#") and len(href) > 1:
                    return href[1:]
            found = _find_fragment_target(child)
            if found is not None:
                return found
    return None


def _attribute(node: ElementNode, name: str) -> str | None:
    for attribute_name, value in node.attributes:
        if attribute_name == name:
            return value
    return None


def _flatten_text(node: ElementNode) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, TextNode):
            parts.append(child.text)
        elif isinstance(child, ElementNode):
            parts.append(_flatten_text(child))
    return "".join(parts).strip()
