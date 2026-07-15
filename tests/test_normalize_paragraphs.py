from __future__ import annotations

import pytest

from wikiepwing.model.inline import TextInline
from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.paragraphs import (
    convert_inline_nodes,
    convert_paragraph,
    is_paragraph,
)


def _first_body_child(html: str) -> ElementNode:
    result = parse_html(html, max_dom_depth=32)
    html_node = result.root.children[0]
    assert isinstance(html_node, ElementNode)
    body = html_node.children[0]
    assert isinstance(body, ElementNode)
    child = body.children[0]
    assert isinstance(child, ElementNode)
    return child


def test_is_paragraph_matches_p_element() -> None:
    result = parse_html("<p>text</p>", max_dom_depth=32)
    assert is_paragraph(result.root.children[0])


def test_is_paragraph_rejects_non_p_element() -> None:
    result = parse_html("<div>text</div>", max_dom_depth=32)
    assert not is_paragraph(result.root.children[0])


def test_convert_paragraph_produces_text_inline() -> None:
    p = _first_body_child("<html><body><p>hello world</p></body></html>")

    block, diagnostics = convert_paragraph(p)

    assert block.inlines == (TextInline(value="hello world"),)
    assert diagnostics == ()


def test_convert_paragraph_handles_empty_paragraph() -> None:
    p = _first_body_child("<html><body><p></p></body></html>")

    block, diagnostics = convert_paragraph(p)

    assert block.inlines == ()
    assert diagnostics == ()


def test_convert_paragraph_rejects_non_paragraph_element() -> None:
    div = _first_body_child("<html><body><div>text</div></body></html>")

    with pytest.raises(ValueError, match="not a paragraph element"):
        convert_paragraph(div)


def test_convert_inline_nodes_recurses_transparently_through_unknown_elements() -> None:
    p = _first_body_child('<html><body><p>a <span class="unknown">b</span> c</p></body></html>')

    block, _ = convert_paragraph(p)

    assert block.inlines == (
        TextInline(value="a "),
        TextInline(value="b"),
        TextInline(value=" c"),
    )


def test_convert_inline_nodes_preserves_order_across_nested_unknown_wrappers() -> None:
    p = _first_body_child(
        '<html><body><p>one <a><span class="x">two</span></a> three</p></body></html>'
    )

    block, _ = convert_paragraph(p)

    assert [inline.value for inline in block.inlines] == ["one ", "two", " three"]  # type: ignore[union-attr]


def test_convert_inline_nodes_empty_input_returns_empty_tuple() -> None:
    assert convert_inline_nodes(()) == ()


def test_convert_inline_nodes_converts_inline_math_with_tex_source() -> None:
    from wikiepwing.model.inline import MathInline

    p = _first_body_child(
        "<html><body><p>see "
        '<math><annotation encoding="application/x-tex">x^2</annotation></math>'
        " here</p></body></html>"
    )

    block, _ = convert_paragraph(p)

    assert block.inlines == (
        TextInline(value="see "),
        MathInline(source="x^2", source_format="tex"),
        TextInline(value=" here"),
    )


def test_convert_inline_nodes_math_with_no_source_falls_back_to_unsupported() -> None:
    from wikiepwing.model.inline import UnsupportedInline

    p = _first_body_child("<html><body><p><math></math></p></body></html>")

    block, _ = convert_paragraph(p)

    assert block.inlines == (
        UnsupportedInline(element_name="math", fallback_text="", diagnostic_code="MATH_NO_SOURCE"),
    )
