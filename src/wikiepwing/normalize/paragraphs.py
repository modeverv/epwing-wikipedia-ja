"""Paragraph and generic inline conversion (TASK-G005, ARCHITECTURE.md 12.2 pass N50).

`convert_inline_nodes` is the shared entry point every inline-bearing block
(paragraphs now, headings/list items/etc. later) will use. It currently only
recognizes text nodes; any element it doesn't recognize is treated as a
transparent wrapper and its children are recursed into rather than dropped.
TASK-G006 extends this same dispatch with `<b>`/`<strong>`/`<i>`/`<em>`/
`<code>`/`<br>` handlers.
"""

from __future__ import annotations

from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import Inline, TextInline
from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode


def convert_inline_nodes(nodes: tuple[Node, ...]) -> tuple[Inline, ...]:
    """Convert a sequence of DOM nodes into a flat sequence of Inline values."""
    inlines: list[Inline] = []
    for node in nodes:
        inlines.extend(_convert_one(node))
    return tuple(inlines)


def _convert_one(node: Node) -> tuple[Inline, ...]:
    if isinstance(node, TextNode):
        return (TextInline(value=node.text),) if node.text else ()
    return convert_inline_nodes(node.children)


def is_paragraph(node: Node) -> bool:
    """Return whether `node` is a `<p>` element."""
    return isinstance(node, ElementNode) and node.tag == "p"


def convert_paragraph(node: ElementNode) -> tuple[ParagraphBlock, tuple[Diagnostic, ...]]:
    """Convert one `<p>` element into a ParagraphBlock."""
    if node.tag != "p":
        raise ValueError(f"not a paragraph element: <{node.tag}>")
    inlines = convert_inline_nodes(node.children)
    return ParagraphBlock(inlines=inlines), ()
