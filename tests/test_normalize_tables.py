from __future__ import annotations

import pytest

from wikiepwing.normalize.html_parser import ElementNode, TextNode, parse_html
from wikiepwing.normalize.tables import is_table, parse_table_dom


def _parse_table(html: str) -> ElementNode:
    result = parse_html(html, max_dom_depth=50)
    return _find(result.root, "table")


def _find(node: ElementNode, tag: str) -> ElementNode:
    found = _find_or_none(node, tag)
    if found is None:
        raise AssertionError(f"<{tag}> not found")
    return found


def _find_or_none(node: ElementNode, tag: str) -> ElementNode | None:
    if node.tag == tag:
        return node
    for child in node.children:
        if isinstance(child, ElementNode):
            found = _find_or_none(child, tag)
            if found is not None:
                return found
    return None


def _text(cell_content: tuple[object, ...]) -> str:
    return "".join(node.text for node in cell_content if isinstance(node, TextNode))


def test_is_table_recognizes_table_element() -> None:
    table = _parse_table("<table><tr><td>x</td></tr></table>")

    assert is_table(table) is True


def test_is_table_rejects_non_table_element() -> None:
    div = _find(parse_html("<div>x</div>", max_dom_depth=10).root, "div")

    assert is_table(div) is False


def test_parse_table_dom_rejects_non_table_element() -> None:
    div = _find(parse_html("<div>x</div>", max_dom_depth=10).root, "div")

    with pytest.raises(ValueError, match="not a table"):
        parse_table_dom(div)


def test_parses_simple_rows_and_cells() -> None:
    table = _parse_table(
        "<table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>"
    )

    parsed, diagnostics = parse_table_dom(table)

    assert diagnostics == ()
    assert len(parsed.rows) == 2
    assert [_text(cell.content) for cell in parsed.rows[0].cells] == ["a", "b"]
    assert [_text(cell.content) for cell in parsed.rows[1].cells] == ["c", "d"]


def test_th_cells_are_marked_as_header() -> None:
    table = _parse_table("<table><tr><th>Name</th><td>Value</td></tr></table>")

    parsed, _ = parse_table_dom(table)

    assert parsed.rows[0].cells[0].is_header is True
    assert parsed.rows[0].cells[1].is_header is False


def test_rowspan_and_colspan_are_read() -> None:
    table = _parse_table('<table><tr><td rowspan="2" colspan="3">x</td></tr></table>')

    parsed, diagnostics = parse_table_dom(table)

    assert diagnostics == ()
    cell = parsed.rows[0].cells[0]
    assert cell.row_span == 2
    assert cell.col_span == 3


def test_missing_span_attributes_default_to_one() -> None:
    table = _parse_table("<table><tr><td>x</td></tr></table>")

    parsed, _ = parse_table_dom(table)

    cell = parsed.rows[0].cells[0]
    assert cell.row_span == 1
    assert cell.col_span == 1


def test_invalid_span_falls_back_to_one_with_diagnostic() -> None:
    table = _parse_table('<table><tr><td colspan="not-a-number">x</td></tr></table>')

    parsed, diagnostics = parse_table_dom(table)

    assert parsed.rows[0].cells[0].col_span == 1
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "TABLE_INVALID_SPAN"


def test_non_positive_span_falls_back_to_one_with_diagnostic() -> None:
    table = _parse_table('<table><tr><td rowspan="0">x</td></tr></table>')

    parsed, diagnostics = parse_table_dom(table)

    assert parsed.rows[0].cells[0].row_span == 1
    assert len(diagnostics) == 1


def test_caption_is_captured() -> None:
    table = _parse_table("<table><caption>My Table</caption><tr><td>x</td></tr></table>")

    parsed, _ = parse_table_dom(table)

    assert _text(parsed.caption) == "My Table"


def test_no_caption_is_an_empty_tuple() -> None:
    table = _parse_table("<table><tr><td>x</td></tr></table>")

    parsed, _ = parse_table_dom(table)

    assert parsed.caption == ()


def test_rows_found_within_thead_tbody_tfoot() -> None:
    table = _parse_table(
        "<table>"
        "<thead><tr><th>H</th></tr></thead>"
        "<tbody><tr><td>b</td></tr></tbody>"
        "<tfoot><tr><td>f</td></tr></tfoot>"
        "</table>"
    )

    parsed, _ = parse_table_dom(table)

    assert len(parsed.rows) == 3
    assert parsed.rows[0].cells[0].is_header is True
    assert _text(parsed.rows[1].cells[0].content) == "b"
    assert _text(parsed.rows[2].cells[0].content) == "f"


def test_nested_table_rows_are_not_captured_as_outer_rows() -> None:
    table = _parse_table(
        "<table><tr><td>outer<table><tr><td>inner</td></tr></table></td></tr></table>"
    )

    parsed, _ = parse_table_dom(table)

    assert len(parsed.rows) == 1
    assert len(parsed.rows[0].cells) == 1


def test_source_class_names_are_captured() -> None:
    table = _parse_table('<table class="wikitable sortable"><tr><td>x</td></tr></table>')

    parsed, _ = parse_table_dom(table)

    assert parsed.source_class_names == ("wikitable", "sortable")


def test_no_class_attribute_is_an_empty_tuple() -> None:
    table = _parse_table("<table><tr><td>x</td></tr></table>")

    parsed, _ = parse_table_dom(table)

    assert parsed.source_class_names == ()
