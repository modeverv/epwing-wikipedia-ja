"""Quote/preformatted conversion (TASK-G009, ARCHITECTURE.md 12.2 pass N60).

`<blockquote>` becomes `QuoteBlock`, handling the typical shapes: a run of
`<p>` children (each converted independently) and/or a run of bare inline
content (grouped into one `ParagraphBlock`). `<pre>` becomes
`PreformattedBlock` with its text extracted verbatim -- no whitespace
normalization, per ARCHITECTURE.md 13.1's "本文は過剰にNFKCしません".
"""

from __future__ import annotations

from wikiepwing.model.blocks import Block, ParagraphBlock, PreformattedBlock, QuoteBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode
from wikiepwing.normalize.paragraphs import convert_inline_nodes, convert_paragraph


def is_quote(node: Node) -> bool:
    """Return whether `node` is a `<blockquote>` element."""
    return isinstance(node, ElementNode) and node.tag == "blockquote"


def is_preformatted(node: Node) -> bool:
    """Return whether `node` is a `<pre>` element."""
    return isinstance(node, ElementNode) and node.tag == "pre"


def convert_quote(node: ElementNode) -> tuple[QuoteBlock, tuple[Diagnostic, ...]]:
    """Convert one `<blockquote>` element into a QuoteBlock."""
    if node.tag != "blockquote":
        raise ValueError(f"not a blockquote element: <{node.tag}>")

    blocks: list[Block] = []
    diagnostics: list[Diagnostic] = []
    inline_buffer: list[Node] = []

    def flush() -> None:
        if inline_buffer:
            blocks.append(ParagraphBlock(inlines=convert_inline_nodes(tuple(inline_buffer))))
            inline_buffer.clear()

    for child in node.children:
        if isinstance(child, ElementNode) and child.tag == "p":
            flush()
            paragraph, paragraph_diagnostics = convert_paragraph(child)
            blocks.append(paragraph)
            diagnostics.extend(paragraph_diagnostics)
        else:
            inline_buffer.append(child)
    flush()

    return QuoteBlock(blocks=tuple(blocks)), tuple(diagnostics)


def convert_preformatted(node: ElementNode) -> tuple[PreformattedBlock, tuple[Diagnostic, ...]]:
    """Convert one `<pre>` element into a PreformattedBlock, preserving its text verbatim."""
    if node.tag != "pre":
        raise ValueError(f"not a preformatted element: <{node.tag}>")
    return PreformattedBlock(text=_flatten_text_verbatim(node)), ()


def _flatten_text_verbatim(node: ElementNode) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, TextNode):
            parts.append(child.text)
        elif isinstance(child, ElementNode):
            parts.append(_flatten_text_verbatim(child))
    return "".join(parts)
