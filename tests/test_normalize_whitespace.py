from __future__ import annotations

from wikiepwing.model.blocks import (
    CodeBlock,
    HeadingBlock,
    ListItem,
    ParagraphBlock,
    PreformattedBlock,
    QuoteBlock,
    UnorderedListBlock,
    UnsupportedBlock,
)
from wikiepwing.model.inline import CodeInline, StrongInline, TextInline
from wikiepwing.normalize.whitespace import normalize_block_whitespace, normalize_text


def test_normalize_text_converts_crlf_and_cr_to_lf() -> None:
    assert normalize_text("a\r\nb\rc") == "a b c"


def test_normalize_text_strips_control_characters_but_keeps_newline() -> None:
    assert normalize_text("a\x00b\x1fc\nd") == "abc d"


def test_normalize_text_strips_zero_width_characters() -> None:
    assert normalize_text("a​b‌c‍d﻿e") == "abcde"


def test_normalize_text_collapses_consecutive_whitespace() -> None:
    assert normalize_text("a   b\n\n\tc") == "a b c"


def test_normalize_text_is_idempotent() -> None:
    once = normalize_text("a   b\r\nc")
    assert normalize_text(once) == once


def test_normalize_block_whitespace_normalizes_paragraph_text() -> None:
    block = ParagraphBlock(inlines=(TextInline(value="a   b\r\nc"),))

    result = normalize_block_whitespace(block)

    assert result == ParagraphBlock(inlines=(TextInline(value="a b c"),))


def test_normalize_block_whitespace_normalizes_nested_strong_inline() -> None:
    block = ParagraphBlock(inlines=(StrongInline(inlines=(TextInline(value="a   b"),)),))

    result = normalize_block_whitespace(block)

    assert result == ParagraphBlock(inlines=(StrongInline(inlines=(TextInline(value="a b"),)),))


def test_normalize_block_whitespace_normalizes_heading() -> None:
    block = HeadingBlock(level=2, anchor="x", inlines=(TextInline(value="a   b"),))

    result = normalize_block_whitespace(block)

    assert result == HeadingBlock(level=2, anchor="x", inlines=(TextInline(value="a b"),))


def test_normalize_block_whitespace_normalizes_list_items() -> None:
    block = UnorderedListBlock(
        items=(ListItem(blocks=(ParagraphBlock(inlines=(TextInline(value="a   b"),)),)),)
    )

    result = normalize_block_whitespace(block)

    assert result.items[0].blocks[0] == ParagraphBlock(inlines=(TextInline(value="a b"),))


def test_normalize_block_whitespace_normalizes_quote_contents() -> None:
    block = QuoteBlock(blocks=(ParagraphBlock(inlines=(TextInline(value="a   b"),)),))

    result = normalize_block_whitespace(block)

    assert result == QuoteBlock(blocks=(ParagraphBlock(inlines=(TextInline(value="a b"),)),))


def test_normalize_block_whitespace_leaves_preformatted_text_untouched() -> None:
    block = PreformattedBlock(text="  raw   text\n\nwith  spaces  ")

    result = normalize_block_whitespace(block)

    assert result == block


def test_normalize_block_whitespace_leaves_code_block_text_untouched() -> None:
    block = CodeBlock(text="  raw   code  ", language="python")

    result = normalize_block_whitespace(block)

    assert result == block


def test_normalize_block_whitespace_leaves_code_inline_untouched() -> None:
    block = ParagraphBlock(inlines=(CodeInline(value="  raw   code  "),))

    result = normalize_block_whitespace(block)

    assert result == block


def test_normalize_block_whitespace_normalizes_unsupported_fallback_text() -> None:
    block = UnsupportedBlock(
        element_name="table", fallback_text="a   b\r\nc", diagnostic_code="DOM_UNKNOWN_ELEMENT"
    )

    result = normalize_block_whitespace(block)

    assert isinstance(result, UnsupportedBlock)
    assert result.fallback_text == "a b c"
