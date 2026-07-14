"""Block dispatch and unknown-DOM fallback (TASK-G010/K010/L003, ARCHITECTURE.md 12.2).

`convert_block` ties together every per-element converter built in
TASK-G004-G009 plus `<table>`/infobox conversion (TASK-K001-K009,
TASK-K010 wires them in here) and reference list conversion
(TASK-L001-L002, TASK-L003 wires it in here), falling back to
`UnsupportedBlock` (with a `DOM_UNKNOWN_ELEMENT` diagnostic, matching
ARCHITECTURE.md 11.7's example code) for anything still unrecognized --
images and math, whose real HTML conversion is deferred to later epics
(N/O) per PLAN.md's phased scope. `convert_document` groups runs of bare
text/inline content between block-level siblings into their own
`ParagraphBlock`.

A reference list is itself an `<ol>`, so `is_reference_list` must be
checked *before* `is_ordered_list` -- otherwise every reference list would
be misconverted into a plain OrderedListBlock instead of a ReferencesBlock.

`build_table_block`/`build_infobox_block` are imported inside
`convert_block` rather than at module level: they call back into this
module's own `convert_document` (to convert cell/field content), so a
top-level import would be circular. Deferring the import to call time
breaks the cycle since both modules are already fully loaded by then.
`build_references_block` only needs `convert_inline_nodes`, not
`convert_document`, so it has no such cycle and is imported normally.
"""

from __future__ import annotations

from wikiepwing.model.blocks import Block, HorizontalRuleBlock, ParagraphBlock, UnsupportedBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.definition_lists import convert_definition_list, is_definition_list
from wikiepwing.normalize.headings import convert_heading, is_heading
from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode
from wikiepwing.normalize.infobox import is_infobox
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
from wikiepwing.normalize.reference_list import is_reference_list
from wikiepwing.normalize.references_block import build_references_block
from wikiepwing.normalize.tables import is_table


def convert_block(node: ElementNode) -> tuple[Block, tuple[Diagnostic, ...]]:
    """Convert one block-level element, dispatching to the right converter."""
    if is_heading(node):
        return convert_heading(node)
    if node.tag == "p":
        return ParagraphBlock(inlines=convert_inline_nodes(node.children)), ()
    if is_unordered_list(node):
        return convert_unordered_list(node)
    if is_reference_list(node):
        return build_references_block(node)
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
    if is_infobox(node):
        from wikiepwing.normalize.infobox_block import build_infobox_block

        return build_infobox_block(node)
    if is_table(node):
        from wikiepwing.normalize.table_block import build_table_block

        return build_table_block(node)
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
