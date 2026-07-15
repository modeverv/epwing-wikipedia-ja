"""Paragraph and generic inline conversion (TASK-G005/G006, ARCHITECTURE.md 12.2 pass N50).

`convert_inline_nodes` is the shared entry point every inline-bearing block
(paragraphs now, headings/list items/etc. later) will use. Text nodes become
`TextInline`; `<b>`/`<strong>`, `<i>`/`<em>`, `<code>`, and `<br>` are
recognized (TASK-G006); any other element is treated as a transparent
wrapper and its children are recursed into rather than dropped.
"""

from __future__ import annotations

from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import (
    CodeInline,
    EmphasisInline,
    Inline,
    LineBreakInline,
    MathInline,
    StrongInline,
    TextInline,
    UnsupportedInline,
)
from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode
from wikiepwing.normalize.math_content import resolve_math_source
from wikiepwing.normalize.math_node import is_math_node, parse_math_node

_STRONG_TAGS = frozenset({"b", "strong"})
_EMPHASIS_TAGS = frozenset({"i", "em"})
_MATH_NO_SOURCE_DIAGNOSTIC_CODE = "MATH_NO_SOURCE"


def convert_inline_nodes(nodes: tuple[Node, ...]) -> tuple[Inline, ...]:
    """Convert a sequence of DOM nodes into a flat sequence of Inline values."""
    inlines: list[Inline] = []
    for node in nodes:
        inlines.extend(_convert_one(node))
    return tuple(inlines)


def _convert_one(node: Node) -> tuple[Inline, ...]:
    if isinstance(node, TextNode):
        return (TextInline(value=node.text),) if node.text else ()
    if node.tag in _STRONG_TAGS:
        return (StrongInline(inlines=convert_inline_nodes(node.children)),)
    if node.tag in _EMPHASIS_TAGS:
        return (EmphasisInline(inlines=convert_inline_nodes(node.children)),)
    if node.tag == "code":
        text = _flatten_text(node)
        return (CodeInline(value=text),) if text else ()
    if node.tag == "br":
        return (LineBreakInline(),)
    if is_math_node(node):
        return (_convert_math_inline(node),)
    return convert_inline_nodes(node.children)


def _convert_math_inline(node: ElementNode) -> Inline:
    resolved = resolve_math_source(parse_math_node(node))
    if resolved is None:
        return UnsupportedInline(
            element_name=node.tag,
            fallback_text="",
            diagnostic_code=_MATH_NO_SOURCE_DIAGNOSTIC_CODE,
        )
    source, source_format = resolved
    return MathInline(source=source, source_format=source_format)


def _flatten_text(node: ElementNode) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, TextNode):
            parts.append(child.text)
        elif isinstance(child, ElementNode):
            parts.append(_flatten_text(child))
    return "".join(parts)


def is_paragraph(node: Node) -> bool:
    """Return whether `node` is a `<p>` element."""
    return isinstance(node, ElementNode) and node.tag == "p"


def convert_paragraph(node: ElementNode) -> tuple[ParagraphBlock, tuple[Diagnostic, ...]]:
    """Convert one `<p>` element into a ParagraphBlock."""
    if node.tag != "p":
        raise ValueError(f"not a paragraph element: <{node.tag}>")
    inlines = convert_inline_nodes(node.children)
    return ParagraphBlock(inlines=inlines), ()
