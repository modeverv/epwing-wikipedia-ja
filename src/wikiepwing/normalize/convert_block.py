"""Block dispatch and unknown-DOM fallback (TASK-G010, ARCHITECTURE.md 12.2).

`convert_block` ties together every per-element converter built in
TASK-G004-G009 and falls back to `UnsupportedBlock` (with a
`DOM_UNKNOWN_ELEMENT` diagnostic, matching ARCHITECTURE.md 11.7's example
code) for anything not yet recognized -- including `<table>`, infoboxes,
images, math, and references, whose real HTML conversion is deferred to
later epics (K/L/N/O) per PLAN.md's phased scope. `convert_document` groups
runs of bare text/inline content between block-level siblings into their
own `ParagraphBlock`.
"""

from __future__ import annotations

from wikiepwing.model.blocks import Block, HorizontalRuleBlock, ParagraphBlock, UnsupportedBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.definition_lists import convert_definition_list, is_definition_list
from wikiepwing.normalize.headings import convert_heading, is_heading
from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode
from wikiepwing.normalize.lists import (
    convert_ordered_list,
    convert_unordered_list,
    is_ordered_list,
    is_unordered_list,
)
from wikiepwing.normalize.paragraphs import convert_inline_nodes
from wikiepwing.normalize.quotes import (
    convert_preformatted,
    convert_quote,
    is_preformatted,
    is_quote,
)


def convert_block(node: ElementNode) -> tuple[Block, tuple[Diagnostic, ...]]:
    """Convert one block-level element, dispatching to the right converter."""
    if is_heading(node):
        return convert_heading(node)
    if node.tag == "p":
        return ParagraphBlock(inlines=convert_inline_nodes(node.children)), ()
    if is_unordered_list(node):
        return convert_unordered_list(node)
    if is_ordered_list(node):
        return convert_ordered_list(node)
    if is_definition_list(node):
        return convert_definition_list(node)
    if is_quote(node):
        return convert_quote(node)
    if is_preformatted(node):
        return convert_preformatted(node)
    if node.tag == "hr":
        return HorizontalRuleBlock(), ()
    return _convert_unsupported(node)


def convert_document(nodes: tuple[Node, ...]) -> tuple[tuple[Block, ...], tuple[Diagnostic, ...]]:
    """Convert a sequence of top-level DOM nodes into Blocks.

    Runs of bare text/inline content between block-level elements are grouped
    into a single ParagraphBlock rather than one per node.
    """
    blocks: list[Block] = []
    diagnostics: list[Diagnostic] = []
    inline_buffer: list[Node] = []

    def flush() -> None:
        if inline_buffer:
            blocks.append(ParagraphBlock(inlines=convert_inline_nodes(tuple(inline_buffer))))
            inline_buffer.clear()

    for node in nodes:
        if isinstance(node, ElementNode) and _is_block_level(node):
            flush()
            block, block_diagnostics = convert_block(node)
            blocks.append(block)
            diagnostics.extend(block_diagnostics)
        else:
            inline_buffer.append(node)
    flush()

    return tuple(blocks), tuple(diagnostics)


_ADDITIONAL_BLOCK_TAGS = frozenset(
    {
        "div",
        "table",
        "figure",
        "section",
        "article",
        "aside",
        "nav",
        "header",
        "footer",
        "form",
        "fieldset",
    }
)


def _is_block_level(node: ElementNode) -> bool:
    """Whether `node` should be routed through `convert_block` rather than buffered as inline.

    Covers both the block types with a specific converter and other well-known
    HTML block-level tags (table, div, etc.) that fall back to UnsupportedBlock
    -- distinguishing them from inline-level elements/text that should be
    grouped into a shared ParagraphBlock.
    """
    return (
        is_heading(node)
        or node.tag == "p"
        or is_unordered_list(node)
        or is_ordered_list(node)
        or is_definition_list(node)
        or is_quote(node)
        or is_preformatted(node)
        or node.tag == "hr"
        or node.tag in _ADDITIONAL_BLOCK_TAGS
    )


def _convert_unsupported(node: ElementNode) -> tuple[UnsupportedBlock, tuple[Diagnostic, ...]]:
    fallback_text = _flatten_text(node)
    block = UnsupportedBlock(
        element_name=node.tag,
        fallback_text=fallback_text,
        diagnostic_code="DOM_UNKNOWN_ELEMENT",
    )
    diagnostic = Diagnostic(
        code="DOM_UNKNOWN_ELEMENT",
        severity="warning",
        stage="normalize_convert_block",
        page_id=None,
        title=None,
        message=f"unrecognized element <{node.tag}> converted to a fallback block",
        source_path=None,
        source_excerpt=None,
        details={},
    )
    return block, (diagnostic,)


def _flatten_text(node: ElementNode) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, TextNode):
            parts.append(child.text)
        elif isinstance(child, ElementNode):
            parts.append(_flatten_text(child))
    return "".join(parts).strip()
