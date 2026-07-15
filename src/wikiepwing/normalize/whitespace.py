"""Whitespace normalization (TASK-G011, ARCHITECTURE.md 12.2 pass N120, 13.1).

`normalize_text` implements ARCHITECTURE.md 13.1's stored-body-text
processing: CRLF -> LF, invalid control character removal, a zero-width
character policy, and context-free consecutive-whitespace collapsing.
`normalize_block_whitespace` walks an already-built Block tree and applies
`normalize_text` to prose text (TextInline.value, fallback_text, etc.), but
deliberately leaves verbatim fields untouched: `PreformattedBlock.text`,
`CodeInline.value`, `CodeBlock.text`, and `MathBlock.source` (ARCHITECTURE.md
13.1: "本文は過剰にNFKCしません", and the verbatim-preservation policy
established in TASK-G009). Index-string normalization (13.2) is a separate
function/task and is not implemented here.
"""

from __future__ import annotations

import re

from wikiepwing.model.blocks import (
    Block,
    CodeBlock,
    DefinitionEntry,
    DefinitionListBlock,
    HeadingBlock,
    HorizontalRuleBlock,
    ImageBlock,
    InfoboxBlock,
    InfoboxField,
    ListItem,
    MathBlock,
    OrderedListBlock,
    ParagraphBlock,
    PreformattedBlock,
    QuoteBlock,
    ReferencesBlock,
    TableBlock,
    TableCell,
    UnorderedListBlock,
    UnsupportedBlock,
)
from wikiepwing.model.inline import (
    CodeInline,
    EmphasisInline,
    ExternalLinkInline,
    Inline,
    InternalLinkInline,
    LineBreakInline,
    MathInline,
    StrongInline,
    TextInline,
    UnsupportedInline,
)

_ZERO_WIDTH_CHARS = "​‌‍﻿"  # ZWSP, ZWNJ, ZWJ, BOM
_ZERO_WIDTH_TABLE = str.maketrans("", "", _ZERO_WIDTH_CHARS)
_WHITESPACE_RUN = re.compile(r"[ \t\n\r\f\v]+")


def normalize_text(text: str) -> str:
    """Normalize one run of stored body text per ARCHITECTURE.md 13.1."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(char for char in text if not _is_invalid_control_char(char))
    text = text.translate(_ZERO_WIDTH_TABLE)
    return _WHITESPACE_RUN.sub(" ", text)


def _is_invalid_control_char(char: str) -> bool:
    if char == "\n":
        return False
    codepoint = ord(char)
    return codepoint < 0x20 or 0x7F <= codepoint <= 0x9F


def normalize_block_whitespace(block: Block) -> Block:
    """Recursively normalize whitespace throughout a Block tree."""
    if isinstance(block, ParagraphBlock):
        return ParagraphBlock(inlines=_normalize_inlines(block.inlines))
    if isinstance(block, HeadingBlock):
        return HeadingBlock(
            level=block.level, anchor=block.anchor, inlines=_normalize_inlines(block.inlines)
        )
    if isinstance(block, UnorderedListBlock):
        return UnorderedListBlock(items=tuple(_normalize_list_item(item) for item in block.items))
    if isinstance(block, OrderedListBlock):
        return OrderedListBlock(items=tuple(_normalize_list_item(item) for item in block.items))
    if isinstance(block, DefinitionListBlock):
        return DefinitionListBlock(
            entries=tuple(_normalize_definition_entry(entry) for entry in block.entries)
        )
    if isinstance(block, QuoteBlock):
        return QuoteBlock(blocks=tuple(normalize_block_whitespace(b) for b in block.blocks))
    if isinstance(block, PreformattedBlock):
        return block
    if isinstance(block, CodeBlock):
        return block
    if isinstance(block, HorizontalRuleBlock):
        return block
    if isinstance(block, TableBlock):
        return TableBlock(
            caption=_normalize_inlines(block.caption),
            rows=tuple(tuple(_normalize_table_cell(cell) for cell in row) for row in block.rows),
            source_class_names=block.source_class_names,
            complexity=block.complexity,
        )
    if isinstance(block, InfoboxBlock):
        return InfoboxBlock(
            title=normalize_text(block.title) if block.title is not None else None,
            fields=tuple(_normalize_infobox_field(field) for field in block.fields),
            images=block.images,
        )
    if isinstance(block, ImageBlock):
        return ImageBlock(
            media_id=block.media_id,
            alt_text=normalize_text(block.alt_text) if block.alt_text is not None else None,
        )
    if isinstance(block, MathBlock):
        return block
    if isinstance(block, ReferencesBlock):
        return ReferencesBlock(items=tuple(_normalize_inlines(item) for item in block.items))
    if isinstance(block, UnsupportedBlock):
        return UnsupportedBlock(
            element_name=block.element_name,
            fallback_text=normalize_text(block.fallback_text),
            diagnostic_code=block.diagnostic_code,
        )
    raise AssertionError(f"unhandled block type: {type(block).__name__}")


def _normalize_list_item(item: ListItem) -> ListItem:
    return ListItem(blocks=tuple(normalize_block_whitespace(b) for b in item.blocks))


def _normalize_definition_entry(entry: DefinitionEntry) -> DefinitionEntry:
    return DefinitionEntry(
        terms=tuple(_normalize_inlines(term) for term in entry.terms),
        definitions=tuple(
            tuple(normalize_block_whitespace(b) for b in definition)
            for definition in entry.definitions
        ),
    )


def _normalize_table_cell(cell: TableCell) -> TableCell:
    return TableCell(
        blocks=tuple(normalize_block_whitespace(b) for b in cell.blocks),
        row_span=cell.row_span,
        col_span=cell.col_span,
        is_header=cell.is_header,
    )


def _normalize_infobox_field(field: InfoboxField) -> InfoboxField:
    return InfoboxField(
        name=normalize_text(field.name),
        value=tuple(normalize_block_whitespace(b) for b in field.value),
    )


def _normalize_inlines(inlines: tuple[Inline, ...]) -> tuple[Inline, ...]:
    return tuple(_normalize_inline(inline) for inline in inlines)


def _normalize_inline(inline: Inline) -> Inline:
    if isinstance(inline, TextInline):
        return TextInline(value=normalize_text(inline.value))
    if isinstance(inline, StrongInline):
        return StrongInline(inlines=_normalize_inlines(inline.inlines))
    if isinstance(inline, EmphasisInline):
        return EmphasisInline(inlines=_normalize_inlines(inline.inlines))
    if isinstance(inline, CodeInline):
        return inline
    if isinstance(inline, LineBreakInline):
        return inline
    if isinstance(inline, InternalLinkInline):
        return InternalLinkInline(
            label=_normalize_inlines(inline.label),
            target_title=inline.target_title,
            target_normalized_title=inline.target_normalized_title,
            target_fragment=inline.target_fragment,
            target_page_id=inline.target_page_id,
            resolution=inline.resolution,
        )
    if isinstance(inline, ExternalLinkInline):
        return ExternalLinkInline(label=_normalize_inlines(inline.label), url=inline.url)
    if isinstance(inline, MathInline):
        return inline
    if isinstance(inline, UnsupportedInline):
        return UnsupportedInline(
            element_name=inline.element_name,
            fallback_text=normalize_text(inline.fallback_text),
            diagnostic_code=inline.diagnostic_code,
        )
    raise AssertionError(f"unhandled inline type: {type(inline).__name__}")
