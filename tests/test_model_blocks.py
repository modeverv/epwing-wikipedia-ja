from __future__ import annotations

import pytest

from wikiepwing.model.blocks import (
    BlockError,
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
    block_payload,
    parse_block,
)
from wikiepwing.model.inline import StrongInline, TextInline


def test_paragraph_block_round_trips() -> None:
    block = ParagraphBlock(inlines=(TextInline("hello"),))

    restored = parse_block(block_payload(block))

    assert restored == block
    assert block.payload() == {
        "type": "paragraph",
        "inlines": [{"type": "text", "value": "hello"}],
    }


def test_heading_block_round_trips() -> None:
    block = HeadingBlock(level=2, anchor="history", inlines=(TextInline("History"),))

    restored = parse_block(block_payload(block))

    assert restored == block


def test_heading_block_rejects_invalid_level() -> None:
    with pytest.raises(BlockError, match="level"):
        HeadingBlock(level=0, anchor="x", inlines=())


def test_heading_block_rejects_empty_anchor() -> None:
    with pytest.raises(BlockError, match="anchor"):
        HeadingBlock(level=1, anchor="", inlines=())


def test_unordered_list_block_round_trips_with_nested_paragraph() -> None:
    block = UnorderedListBlock(
        items=(ListItem(blocks=(ParagraphBlock(inlines=(TextInline("item"),)),)),)
    )

    restored = parse_block(block_payload(block))

    assert restored == block


def test_ordered_list_block_round_trips() -> None:
    block = OrderedListBlock(items=(ListItem(blocks=()),))

    restored = parse_block(block_payload(block))

    assert restored == block


def test_definition_list_block_round_trips() -> None:
    block = DefinitionListBlock(
        entries=(
            DefinitionEntry(
                terms=((TextInline("term"),),),
                definitions=((ParagraphBlock(inlines=(TextInline("def"),)),),),
            ),
        )
    )

    restored = parse_block(block_payload(block))

    assert restored == block


def test_quote_block_round_trips_with_nested_blocks() -> None:
    block = QuoteBlock(blocks=(ParagraphBlock(inlines=(TextInline("quoted"),)),))

    restored = parse_block(block_payload(block))

    assert restored == block


def test_preformatted_block_round_trips() -> None:
    block = PreformattedBlock(text="  raw text\n")

    restored = parse_block(block_payload(block))

    assert restored == block


def test_code_block_round_trips_with_language() -> None:
    block = CodeBlock(text="(+ 1 2)", language="lisp")

    restored = parse_block(block_payload(block))

    assert restored == block


def test_code_block_round_trips_without_language() -> None:
    block = CodeBlock(text="raw", language=None)

    restored = parse_block(block_payload(block))

    assert restored == block


def test_horizontal_rule_block_round_trips() -> None:
    block = HorizontalRuleBlock()

    restored = parse_block(block_payload(block))

    assert restored == block
    assert block.payload() == {"type": "horizontal_rule"}


def test_table_block_round_trips_with_nested_cells() -> None:
    block = TableBlock(
        caption=(TextInline("Caption"),),
        rows=(
            (
                TableCell(
                    blocks=(ParagraphBlock(inlines=(TextInline("cell"),)),),
                    row_span=1,
                    col_span=2,
                    is_header=True,
                ),
            ),
        ),
        source_class_names=("wikitable",),
        complexity="simple",
    )

    restored = parse_block(block_payload(block))

    assert restored == block


def test_table_block_rejects_invalid_complexity() -> None:
    with pytest.raises(BlockError, match="complexity"):
        TableBlock(caption=(), rows=(), source_class_names=(), complexity="huge")  # type: ignore[arg-type]


def test_table_cell_rejects_zero_row_span() -> None:
    with pytest.raises(BlockError, match="row_span"):
        TableCell(blocks=(), row_span=0, col_span=1, is_header=False)


def test_table_cell_rejects_zero_col_span() -> None:
    with pytest.raises(BlockError, match="col_span"):
        TableCell(blocks=(), row_span=1, col_span=0, is_header=False)


def test_infobox_block_round_trips_with_nested_field_value() -> None:
    block = InfoboxBlock(
        title="Emacs",
        fields=(
            InfoboxField(
                name="Developer",
                value=(ParagraphBlock(inlines=(TextInline("GNU Project"),)),),
            ),
        ),
        images=("Emacs-logo.svg",),
    )

    restored = parse_block(block_payload(block))

    assert restored == block


def test_infobox_block_round_trips_with_no_title() -> None:
    block = InfoboxBlock(title=None, fields=(), images=())

    restored = parse_block(block_payload(block))

    assert restored == block


def test_infobox_field_rejects_empty_name() -> None:
    with pytest.raises(BlockError, match="name"):
        InfoboxField(name="", value=())


def test_image_block_round_trips() -> None:
    block = ImageBlock(media_id="File:Emacs.png", alt_text="Emacs screenshot")

    restored = parse_block(block_payload(block))

    assert restored == block


def test_image_block_rejects_empty_media_id() -> None:
    with pytest.raises(BlockError, match="media_id"):
        ImageBlock(media_id="", alt_text=None)


def test_math_block_round_trips() -> None:
    block = MathBlock(source="E = mc^2", source_format="tex")

    restored = parse_block(block_payload(block))

    assert restored == block


def test_math_block_rejects_empty_source_format() -> None:
    with pytest.raises(BlockError, match="source_format"):
        MathBlock(source="x", source_format="")


def test_references_block_round_trips() -> None:
    block = ReferencesBlock(items=((TextInline("Some citation"),),))

    restored = parse_block(block_payload(block))

    assert restored == block


def test_unsupported_block_round_trips() -> None:
    block = UnsupportedBlock(
        element_name="video",
        fallback_text="",
        diagnostic_code="DOM_UNSUPPORTED_ELEMENT",
    )

    restored = parse_block(block_payload(block))

    assert restored == block


def test_unsupported_block_rejects_empty_element_name() -> None:
    with pytest.raises(BlockError, match="element_name"):
        UnsupportedBlock(element_name="", fallback_text="", diagnostic_code="X")


def test_parse_block_rejects_non_object() -> None:
    with pytest.raises(BlockError, match="JSON object"):
        parse_block(["not", "an", "object"])


def test_parse_block_rejects_unknown_type() -> None:
    with pytest.raises(BlockError, match="unknown block type"):
        parse_block({"type": "notice"})


def test_parse_block_rejects_missing_type() -> None:
    with pytest.raises(BlockError, match="unknown block type"):
        parse_block({"text": "x"})


def test_nested_strong_inside_paragraph_round_trips() -> None:
    block = ParagraphBlock(inlines=(StrongInline(inlines=(TextInline("bold"),)),))

    restored = parse_block(block_payload(block))

    assert restored == block


def test_list_item_missing_blocks_field_is_rejected() -> None:
    payload = {"type": "unordered_list", "items": [{}]}

    with pytest.raises(BlockError, match="blocks"):
        parse_block(payload)


def test_quote_block_missing_blocks_field_is_rejected() -> None:
    with pytest.raises(BlockError, match="blocks"):
        parse_block({"type": "quote"})
