"""List conversion (TASK-G007, ARCHITECTURE.md 12.2 pass N60).

Converts `<ul>`/`<ol>` into `UnorderedListBlock`/`OrderedListBlock`. Each
`<li>` is handled for the common real-world shape: a run of inline content
(text and inline markup) optionally followed/interrupted by a nested
`<ul>`/`<ol>`. The inline run becomes one `ParagraphBlock`; nested lists
become their own `Block` alongside it. A general "route any DOM node to the
right Block type" dispatcher is out of scope here (TASK-G010/G012).
"""

from __future__ import annotations

from wikiepwing.model.blocks import (
    Block,
    ListItem,
    OrderedListBlock,
    ParagraphBlock,
    UnorderedListBlock,
)
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.html_parser import ElementNode, Node
from wikiepwing.normalize.paragraphs import convert_inline_nodes


def is_unordered_list(node: Node) -> bool:
    """Return whether `node` is a `<ul>` element."""
    return isinstance(node, ElementNode) and node.tag == "ul"


def is_ordered_list(node: Node) -> bool:
    """Return whether `node` is an `<ol>` element."""
    return isinstance(node, ElementNode) and node.tag == "ol"


def convert_unordered_list(
    node: ElementNode,
) -> tuple[UnorderedListBlock, tuple[Diagnostic, ...]]:
    """Convert one `<ul>` element into an UnorderedListBlock."""
    if node.tag != "ul":
        raise ValueError(f"not an unordered list element: <{node.tag}>")
    items, diagnostics = _convert_items(node)
    return UnorderedListBlock(items=items), diagnostics


def convert_ordered_list(node: ElementNode) -> tuple[OrderedListBlock, tuple[Diagnostic, ...]]:
    """Convert one `<ol>` element into an OrderedListBlock."""
    if node.tag != "ol":
        raise ValueError(f"not an ordered list element: <{node.tag}>")
    items, diagnostics = _convert_items(node)
    return OrderedListBlock(items=items), diagnostics


def _convert_items(node: ElementNode) -> tuple[tuple[ListItem, ...], tuple[Diagnostic, ...]]:
    items: list[ListItem] = []
    diagnostics: list[Diagnostic] = []
    for child in node.children:
        if isinstance(child, ElementNode) and child.tag == "li":
            item, item_diagnostics = _convert_list_item(child)
            items.append(item)
            diagnostics.extend(item_diagnostics)
    return tuple(items), tuple(diagnostics)


def _convert_list_item(li: ElementNode) -> tuple[ListItem, tuple[Diagnostic, ...]]:
    blocks: list[Block] = []
    diagnostics: list[Diagnostic] = []
    inline_buffer: list[Node] = []

    def flush() -> None:
        if inline_buffer:
            blocks.append(ParagraphBlock(inlines=convert_inline_nodes(tuple(inline_buffer))))
            inline_buffer.clear()

    for child in li.children:
        if isinstance(child, ElementNode) and child.tag == "ul":
            flush()
            nested, nested_diagnostics = convert_unordered_list(child)
            blocks.append(nested)
            diagnostics.extend(nested_diagnostics)
        elif isinstance(child, ElementNode) and child.tag == "ol":
            flush()
            nested_ordered, nested_ordered_diagnostics = convert_ordered_list(child)
            blocks.append(nested_ordered)
            diagnostics.extend(nested_ordered_diagnostics)
        else:
            inline_buffer.append(child)
    flush()

    return ListItem(blocks=tuple(blocks)), tuple(diagnostics)
