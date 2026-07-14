from __future__ import annotations

import pytest

from wikiepwing.normalize.headings import convert_heading, is_heading
from wikiepwing.normalize.html_parser import ElementNode, parse_html


def _first_heading(html: str) -> ElementNode:
    result = parse_html(html, max_dom_depth=32)
    html_node = result.root.children[0]
    assert isinstance(html_node, ElementNode)
    body = html_node.children[0]
    assert isinstance(body, ElementNode)
    heading = body.children[0]
    assert isinstance(heading, ElementNode)
    return heading


def test_is_heading_matches_h1_through_h6() -> None:
    for level in range(1, 7):
        result = parse_html(f"<h{level}>text</h{level}>", max_dom_depth=32)
        node = result.root.children[0]
        assert is_heading(node)


def test_is_heading_rejects_non_heading() -> None:
    result = parse_html("<p>text</p>", max_dom_depth=32)
    assert not is_heading(result.root.children[0])


def test_convert_heading_uses_own_id_attribute() -> None:
    heading = _first_heading('<html><body><h2 id="History">History</h2></body></html>')

    block, diagnostics = convert_heading(heading)

    assert block.level == 2
    assert block.anchor == "History"
    assert diagnostics == ()


def test_convert_heading_uses_nested_span_id() -> None:
    heading = _first_heading(
        '<html><body><h2><span class="mw-headline" id="History">History</span></h2></body></html>'
    )

    block, diagnostics = convert_heading(heading)

    assert block.anchor == "History"
    assert diagnostics == ()


def test_convert_heading_falls_back_to_slugified_text() -> None:
    heading = _first_heading("<html><body><h3>Early Life</h3></body></html>")

    block, diagnostics = convert_heading(heading)

    assert block.anchor == "Early_Life"
    assert diagnostics == ()


def test_convert_heading_flattens_nested_formatting_to_text() -> None:
    heading = _first_heading("<html><body><h2>Foo <i>bar</i> baz</h2></body></html>")

    block, _ = convert_heading(heading)

    assert len(block.inlines) == 1
    assert block.inlines[0].value == "Foo bar baz"  # type: ignore[union-attr]


def test_convert_heading_records_diagnostic_for_empty_heading() -> None:
    heading = _first_heading("<html><body><h4></h4></body></html>")

    block, diagnostics = convert_heading(heading)

    assert block.anchor == "section"
    assert block.inlines == ()
    codes = {d.code for d in diagnostics}
    assert "DOM_HEADING_ANCHOR_FALLBACK" in codes
    assert "DOM_EMPTY_HEADING" in codes


def test_convert_heading_rejects_non_heading_element() -> None:
    result = parse_html("<p>text</p>", max_dom_depth=32)
    node = result.root.children[0]
    assert isinstance(node, ElementNode)

    with pytest.raises(ValueError, match="not a heading element"):
        convert_heading(node)
