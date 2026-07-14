from __future__ import annotations

from wikiepwing.model.blocks import (
    HeadingBlock,
    HorizontalRuleBlock,
    InfoboxBlock,
    OrderedListBlock,
    ParagraphBlock,
    PreformattedBlock,
    QuoteBlock,
    ReferencesBlock,
    TableBlock,
    UnorderedListBlock,
    UnsupportedBlock,
)
from wikiepwing.model.inline import TextInline
from wikiepwing.normalize.convert_block import convert_block, convert_document
from wikiepwing.normalize.html_parser import ElementNode, parse_html


def _body_children(html: str) -> tuple[ElementNode, ...]:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=32)
    html_node = result.root.children[0]
    assert isinstance(html_node, ElementNode)
    body = html_node.children[0]
    assert isinstance(body, ElementNode)
    return body.children  # type: ignore[return-value]


def test_convert_block_dispatches_heading() -> None:
    node = _body_children("<h2>Title</h2>")[0]
    assert isinstance(node, ElementNode)

    block, diagnostics = convert_block(node)

    assert isinstance(block, HeadingBlock)
    assert diagnostics == ()


def test_convert_block_dispatches_paragraph() -> None:
    node = _body_children("<p>text</p>")[0]
    assert isinstance(node, ElementNode)

    block, diagnostics = convert_block(node)

    assert block == ParagraphBlock(inlines=(TextInline(value="text"),))
    assert diagnostics == ()


def test_convert_block_dispatches_unordered_list() -> None:
    node = _body_children("<ul><li>a</li></ul>")[0]
    assert isinstance(node, ElementNode)

    block, diagnostics = convert_block(node)

    assert isinstance(block, UnorderedListBlock)
    assert diagnostics == ()


def test_convert_block_dispatches_quote() -> None:
    node = _body_children("<blockquote><p>x</p></blockquote>")[0]
    assert isinstance(node, ElementNode)

    block, diagnostics = convert_block(node)

    assert isinstance(block, QuoteBlock)
    assert diagnostics == ()


def test_convert_block_dispatches_preformatted() -> None:
    node = _body_children("<pre>raw</pre>")[0]
    assert isinstance(node, ElementNode)

    block, diagnostics = convert_block(node)

    assert isinstance(block, PreformattedBlock)
    assert diagnostics == ()


def test_convert_block_converts_hr_to_horizontal_rule() -> None:
    node = _body_children("<hr>")[0]
    assert isinstance(node, ElementNode)

    block, diagnostics = convert_block(node)

    assert block == HorizontalRuleBlock()
    assert diagnostics == ()


def test_convert_block_falls_back_for_unknown_element() -> None:
    node = _body_children("<div>cell</div>")[0]
    assert isinstance(node, ElementNode)

    block, diagnostics = convert_block(node)

    assert isinstance(block, UnsupportedBlock)
    assert block.element_name == "div"
    assert block.diagnostic_code == "DOM_UNKNOWN_ELEMENT"
    assert "cell" in block.fallback_text
    codes = {d.code for d in diagnostics}
    assert "DOM_UNKNOWN_ELEMENT" in codes


def test_convert_block_dispatches_table_elements() -> None:
    node = _body_children("<table><tr><td>cell</td></tr></table>")[0]
    assert isinstance(node, ElementNode)

    block, diagnostics = convert_block(node)

    assert isinstance(block, TableBlock)
    assert block.complexity == "simple"
    assert diagnostics == ()


def test_convert_block_dispatches_infobox_tables() -> None:
    node = _body_children('<table class="infobox"><tr><th colspan="2">Emacs</th></tr></table>')[0]
    assert isinstance(node, ElementNode)

    block, _ = convert_block(node)

    assert isinstance(block, InfoboxBlock)
    assert block.title == "Emacs"


def test_convert_block_dispatches_reference_lists() -> None:
    node = _body_children(
        '<ol class="references">'
        '<li id="cite_note-1"><span class="reference-text">Citation.</span></li>'
        "</ol>"
    )[0]
    assert isinstance(node, ElementNode)

    block, diagnostics = convert_block(node)

    assert isinstance(block, ReferencesBlock)
    assert block.items == ((TextInline(value="Citation."),),)
    assert diagnostics == ()


def test_convert_block_dispatches_plain_ordered_lists_as_before() -> None:
    node = _body_children("<ol><li>a</li></ol>")[0]
    assert isinstance(node, ElementNode)

    block, _ = convert_block(node)

    assert isinstance(block, OrderedListBlock)


def test_convert_document_groups_bare_text_between_block_elements() -> None:
    nodes = _body_children("<h2>Title</h2>lead in text<p>formal paragraph</p>")

    blocks, diagnostics = convert_document(nodes)

    assert diagnostics == ()
    assert isinstance(blocks[0], HeadingBlock)
    assert blocks[1] == ParagraphBlock(inlines=(TextInline(value="lead in text"),))
    assert blocks[2] == ParagraphBlock(inlines=(TextInline(value="formal paragraph"),))


def test_convert_document_groups_bare_inline_runs_together() -> None:
    nodes = _body_children("one <b>two</b> three<h2>Heading</h2>")

    blocks, _ = convert_document(nodes)

    from wikiepwing.model.inline import StrongInline

    assert blocks[0] == ParagraphBlock(
        inlines=(
            TextInline(value="one "),
            StrongInline(inlines=(TextInline(value="two"),)),
            TextInline(value=" three"),
        )
    )
    assert isinstance(blocks[1], HeadingBlock)


def test_convert_document_empty_input() -> None:
    blocks, diagnostics = convert_document(())

    assert blocks == ()
    assert diagnostics == ()


def test_convert_document_propagates_fallback_diagnostics() -> None:
    nodes = _body_children("<div>x</div>")

    blocks, diagnostics = convert_document(nodes)

    assert isinstance(blocks[0], UnsupportedBlock)
    codes = {d.code for d in diagnostics}
    assert "DOM_UNKNOWN_ELEMENT" in codes
