"""Reference list parser (TASK-L002, ARCHITECTURE.md 12.2 "N100 Convert references").

MediaWiki's Cite extension renders the end-of-article reference list as
`<ol class="references"><li id="cite_note-X"><span class="mw-cite-
backlink">...</span><span class="reference-text">actual citation</span>
</li>...</ol>` -- no algorithm for this is specified elsewhere, so this
module relies on that stable, well-known convention (the same one
TASK-L001 documents for the inline marker side). Each `<li>`'s `id`
matches a `cite_note-...` target a TASK-L001 marker's `target_id` may
point to.
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.normalize.html_parser import ElementNode, Node, has_class

_LIST_TAG = "ol"
_LIST_CLASS = "references"
_BACKLINK_CLASS = "mw-cite-backlink"
_TEXT_CLASS = "reference-text"


@dataclass(frozen=True, slots=True)
class RawReferenceItem:
    """One reference-list entry's note id and citation content."""

    note_id: str | None
    content: tuple[Node, ...]


def is_reference_list(node: Node) -> bool:
    """Return whether `node` is an `<ol class="references">` reference list."""
    return isinstance(node, ElementNode) and node.tag == _LIST_TAG and has_class(node, _LIST_CLASS)


def parse_reference_list(node: ElementNode) -> tuple[RawReferenceItem, ...]:
    """Parse a reference list `<ol>` element into its RawReferenceItems."""
    if not (node.tag == _LIST_TAG and has_class(node, _LIST_CLASS)):
        raise ValueError(f"not a reference list element: <{node.tag}>")
    return tuple(
        _parse_item(child)
        for child in node.children
        if isinstance(child, ElementNode) and child.tag == "li"
    )


def _parse_item(li: ElementNode) -> RawReferenceItem:
    note_id = _attribute(li, "id")
    text_span = _find_child_with_class(li, _TEXT_CLASS)
    if text_span is not None:
        return RawReferenceItem(note_id=note_id, content=text_span.children)
    content = tuple(
        child
        for child in li.children
        if not (isinstance(child, ElementNode) and has_class(child, _BACKLINK_CLASS))
    )
    return RawReferenceItem(note_id=note_id, content=content)


def _find_child_with_class(node: ElementNode, class_name: str) -> ElementNode | None:
    for child in node.children:
        if isinstance(child, ElementNode) and has_class(child, class_name):
            return child
    return None


def _attribute(node: ElementNode, name: str) -> str | None:
    for attribute_name, value in node.attributes:
        if attribute_name == name:
            return value
    return None
