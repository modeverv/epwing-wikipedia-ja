from __future__ import annotations

from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.inline import TextInline
from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.table_block import build_table_block


def _parse_table(html: str) -> ElementNode:
    result = parse_html(html, max_dom_depth=50)
    return _find(result.root, "table")


def _find(node: ElementNode, tag: str) -> ElementNode:
    if node.tag == tag:
        return node
    for child in node.children:
        if isinstance(child, ElementNode):
            found = _find_or_none(child, tag)
            if found is not None:
                return found
    raise AssertionError(f"<{tag}> not found")


def _find_or_none(node: ElementNode, tag: str) -> ElementNode | None:
    if node.tag == tag:
        return node
    for child in node.children:
        if isinstance(child, ElementNode):
            found = _find_or_none(child, tag)
            if found is not None:
                return found
    return None


def test_builds_a_simple_table_block() -> None:
    table = _parse_table("<table><tr><td>a</td><td>b</td></tr></table>")

    block, diagnostics = build_table_block(table)

    assert diagnostics == ()
    assert block.complexity == "simple"
    assert len(block.rows) == 1
    assert len(block.rows[0]) == 2


def test_cell_content_is_converted_to_blocks() -> None:
    table = _parse_table("<table><tr><td><p>hello</p></td></tr></table>")

    block, _ = build_table_block(table)

    cell_blocks = block.rows[0][0].blocks
    assert len(cell_blocks) == 1
    paragraph = cell_blocks[0]
    assert isinstance(paragraph, ParagraphBlock)
    assert paragraph.inlines == (TextInline(value="hello"),)


def test_caption_is_converted_to_inlines() -> None:
    table = _parse_table("<table><caption>My Table</caption><tr><td>x</td></tr></table>")

    block, _ = build_table_block(table)

    assert block.caption == (TextInline(value="My Table"),)


def test_header_and_span_are_preserved_on_the_cell() -> None:
    table = _parse_table('<table><tr><th colspan="2">H</th></tr></table>')

    block, _ = build_table_block(table)

    cell = block.rows[0][0]
    assert cell.is_header is True
    assert cell.col_span == 2


def test_class_names_are_preserved() -> None:
    table = _parse_table('<table class="wikitable"><tr><td>x</td></tr></table>')

    block, _ = build_table_block(table)

    assert block.source_class_names == ("wikitable",)


def test_wide_table_is_classified_accordingly() -> None:
    cells = "".join(f"<td>{i}</td>" for i in range(8))
    table = _parse_table(f"<table><tr>{cells}</tr></table>")

    block, _ = build_table_block(table)

    assert block.complexity == "wide"


def test_table_with_rowspan_is_classified_complex() -> None:
    table = _parse_table('<table><tr><td rowspan="2">x</td></tr><tr></tr></table>')

    block, _ = build_table_block(table)

    assert block.complexity == "complex"


def test_empty_table_is_unsupported() -> None:
    table = _parse_table("<table></table>")

    block, _ = build_table_block(table)

    assert block.complexity == "unsupported"
    assert block.rows == ()


def test_invalid_span_diagnostic_is_propagated() -> None:
    table = _parse_table('<table><tr><td colspan="bogus">x</td></tr></table>')

    _, diagnostics = build_table_block(table)

    assert any(diagnostic.code == "TABLE_INVALID_SPAN" for diagnostic in diagnostics)
