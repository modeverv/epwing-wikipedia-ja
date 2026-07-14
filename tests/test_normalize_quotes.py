from __future__ import annotations

import pytest

from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.inline import TextInline
from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.quotes import (
    convert_preformatted,
    convert_quote,
    is_preformatted,
    is_quote,
)


def _first_body_child(html: str) -> ElementNode:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=32)
    html_node = result.root.children[0]
    assert isinstance(html_node, ElementNode)
    body = html_node.children[0]
    assert isinstance(body, ElementNode)
    child = body.children[0]
    assert isinstance(child, ElementNode)
    return child


def test_is_quote_matches_blockquote() -> None:
    bq = _first_body_child("<blockquote><p>x</p></blockquote>")
    assert is_quote(bq)
    assert not is_preformatted(bq)


def test_is_preformatted_matches_pre() -> None:
    pre = _first_body_child("<pre>x</pre>")
    assert is_preformatted(pre)
    assert not is_quote(pre)


def test_convert_quote_with_single_paragraph() -> None:
    bq = _first_body_child("<blockquote><p>quoted text</p></blockquote>")

    block, diagnostics = convert_quote(bq)

    assert diagnostics == ()
    assert block.blocks == (ParagraphBlock(inlines=(TextInline(value="quoted text"),)),)


def test_convert_quote_with_multiple_paragraphs() -> None:
    bq = _first_body_child("<blockquote><p>first</p><p>second</p></blockquote>")

    block, _ = convert_quote(bq)

    assert block.blocks == (
        ParagraphBlock(inlines=(TextInline(value="first"),)),
        ParagraphBlock(inlines=(TextInline(value="second"),)),
    )


def test_convert_quote_with_bare_inline_content() -> None:
    bq = _first_body_child("<blockquote>bare text</blockquote>")

    block, _ = convert_quote(bq)

    assert block.blocks == (ParagraphBlock(inlines=(TextInline(value="bare text"),)),)


def test_convert_quote_separates_bare_content_from_paragraphs() -> None:
    bq = _first_body_child("<blockquote>lead in<p>formal quote</p></blockquote>")

    block, _ = convert_quote(bq)

    assert block.blocks == (
        ParagraphBlock(inlines=(TextInline(value="lead in"),)),
        ParagraphBlock(inlines=(TextInline(value="formal quote"),)),
    )


def test_convert_quote_rejects_non_blockquote_element() -> None:
    p = _first_body_child("<p>text</p>")

    with pytest.raises(ValueError, match="not a blockquote element"):
        convert_quote(p)


def test_convert_preformatted_preserves_whitespace_verbatim() -> None:
    pre = _first_body_child("<pre>  line one\n  line two  </pre>")

    block, diagnostics = convert_preformatted(pre)

    assert block.text == "  line one\n  line two  "
    assert diagnostics == ()


def test_convert_preformatted_flattens_nested_elements_to_text() -> None:
    pre = _first_body_child("<pre>int <b>main</b>()</pre>")

    block, _ = convert_preformatted(pre)

    assert block.text == "int main()"


def test_convert_preformatted_rejects_non_pre_element() -> None:
    p = _first_body_child("<p>text</p>")

    with pytest.raises(ValueError, match="not a preformatted element"):
        convert_preformatted(p)
