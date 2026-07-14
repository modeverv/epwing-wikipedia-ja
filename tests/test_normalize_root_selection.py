from __future__ import annotations

from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.root_selection import select_root_content


def test_select_root_content_prefers_mw_parser_output() -> None:
    html = (
        "<html><body>"
        '<div class="header">ignored</div>'
        '<div class="mw-parser-output"><p>real content</p></div>'
        "</body></html>"
    )
    result = parse_html(html, max_dom_depth=32)

    content = select_root_content(result.root)

    assert len(content) == 1
    assert isinstance(content[0], ElementNode)
    assert content[0].tag == "p"


def test_select_root_content_falls_back_to_body_without_wrapper() -> None:
    html = "<html><body><p>plain body content</p></body></html>"
    result = parse_html(html, max_dom_depth=32)

    content = select_root_content(result.root)

    assert len(content) == 1
    assert isinstance(content[0], ElementNode)
    assert content[0].tag == "p"


def test_select_root_content_falls_back_to_document_without_body() -> None:
    html = "<p>fragment with no html/body wrapper</p>"
    result = parse_html(html, max_dom_depth=32)

    content = select_root_content(result.root)

    assert len(content) == 1
    assert isinstance(content[0], ElementNode)
    assert content[0].tag == "p"


def test_select_root_content_detects_mw_parser_output_nested_in_body() -> None:
    html = (
        '<html><body><div><div class="other mw-parser-output extra">'
        "<p>nested content</p></div></div></body></html>"
    )
    result = parse_html(html, max_dom_depth=32)

    content = select_root_content(result.root)

    assert len(content) == 1
    assert isinstance(content[0], ElementNode)
    assert content[0].tag == "p"


def test_select_root_content_class_token_match_is_exact() -> None:
    html = '<html><body><div class="mw-parser-output-extra"><p>decoy</p></div></body></html>'
    result = parse_html(html, max_dom_depth=32)

    content = select_root_content(result.root)

    div = content[0]
    assert isinstance(div, ElementNode)
    assert div.tag == "div"
