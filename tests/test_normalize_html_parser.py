from __future__ import annotations

import pytest

from wikiepwing.normalize.html_parser import (
    ElementNode,
    HtmlParseError,
    TextNode,
    parse_html,
)


def test_parse_html_builds_element_tree() -> None:
    result = parse_html("<p>hello <b>world</b></p>", max_dom_depth=32)

    assert result.diagnostics == ()
    p = result.root.children[0]
    assert isinstance(p, ElementNode)
    assert p.tag == "p"
    assert p.children[0] == TextNode(text="hello ")
    b = p.children[1]
    assert isinstance(b, ElementNode)
    assert b.tag == "b"
    assert b.children == (TextNode(text="world"),)


def test_parse_html_preserves_attributes() -> None:
    result = parse_html('<a href="https://example.org">link</a>', max_dom_depth=32)

    a = result.root.children[0]
    assert isinstance(a, ElementNode)
    assert a.attributes == (("href", "https://example.org"),)


def test_parse_html_handles_void_elements_without_end_tag() -> None:
    result = parse_html("<p>line one<br>line two</p>", max_dom_depth=32)

    p = result.root.children[0]
    assert isinstance(p, ElementNode)
    assert [type(child).__name__ for child in p.children] == ["TextNode", "ElementNode", "TextNode"]
    br = p.children[1]
    assert isinstance(br, ElementNode)
    assert br.tag == "br"
    assert br.children == ()


def test_parse_html_handles_self_closing_tags() -> None:
    result = parse_html('<img src="x.png"/>', max_dom_depth=32)

    img = result.root.children[0]
    assert isinstance(img, ElementNode)
    assert img.tag == "img"


def test_parse_html_ignores_comments_and_declarations() -> None:
    result = parse_html("<!DOCTYPE html><!-- a comment --><p>text</p>", max_dom_depth=32)

    assert len(result.root.children) == 1
    assert result.root.children[0] == ElementNode(
        tag="p", attributes=(), children=(TextNode(text="text"),)
    )


def test_parse_html_decodes_entities_without_network() -> None:
    result = parse_html("<p>&amp;&lt;&gt;&#65;</p>", max_dom_depth=32)

    p = result.root.children[0]
    assert isinstance(p, ElementNode)
    assert p.children == (TextNode(text="&<>A"),)


def test_parse_html_recovers_from_unmatched_end_tag() -> None:
    result = parse_html("<p>text</div></p>", max_dom_depth=32)

    codes = {d.code for d in result.diagnostics}
    assert "DOM_UNMATCHED_END_TAG" in codes
    p = result.root.children[0]
    assert isinstance(p, ElementNode)
    assert p.tag == "p"


def test_parse_html_recovers_from_unclosed_nested_tag() -> None:
    result = parse_html("<div><b>bold</div>", max_dom_depth=32)

    codes = [d.code for d in result.diagnostics]
    assert "DOM_UNCLOSED_TAG" in codes
    div = result.root.children[0]
    assert isinstance(div, ElementNode)
    assert div.tag == "div"
    b = div.children[0]
    assert isinstance(b, ElementNode)
    assert b.tag == "b"


def test_parse_html_recovers_from_unclosed_tag_at_eof() -> None:
    result = parse_html("<div><p>text", max_dom_depth=32)

    codes = [d.code for d in result.diagnostics]
    assert codes.count("DOM_UNCLOSED_TAG") == 2
    div = result.root.children[0]
    assert isinstance(div, ElementNode)
    assert div.tag == "div"


def test_parse_html_raises_on_unmatched_end_tag_without_recovery() -> None:
    with pytest.raises(HtmlParseError, match="unmatched closing tag"):
        parse_html("<p>text</div></p>", max_dom_depth=32, html_recover=False)


def test_parse_html_raises_on_unclosed_tag_without_recovery() -> None:
    with pytest.raises(HtmlParseError, match="unclosed element"):
        parse_html("<div><p>text", max_dom_depth=32, html_recover=False)


def test_parse_html_truncates_beyond_max_dom_depth() -> None:
    nested = "<div>" * 5 + "deep" + "</div>" * 5
    result = parse_html(nested, max_dom_depth=2)

    codes = {d.code for d in result.diagnostics}
    assert "DOM_MAX_DEPTH_EXCEEDED" in codes

    def depth(node: ElementNode) -> int:
        max_child_depth = 0
        for child in node.children:
            if isinstance(child, ElementNode):
                max_child_depth = max(max_child_depth, depth(child))
        return 1 + max_child_depth

    assert depth(result.root.children[0]) == 2  # type: ignore[arg-type]


def test_parse_html_raises_on_depth_exceeded_without_recovery() -> None:
    nested = "<div>" * 5 + "deep" + "</div>" * 5
    with pytest.raises(HtmlParseError, match="max_dom_depth"):
        parse_html(nested, max_dom_depth=2, html_recover=False)


def test_parse_html_rejects_non_positive_max_dom_depth() -> None:
    with pytest.raises(HtmlParseError, match="max_dom_depth"):
        parse_html("<p>x</p>", max_dom_depth=0)


def test_parse_html_handles_empty_document() -> None:
    result = parse_html("", max_dom_depth=32)

    assert result.root.children == ()
    assert result.diagnostics == ()
