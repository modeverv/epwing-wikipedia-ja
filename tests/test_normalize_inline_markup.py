from __future__ import annotations

from wikiepwing.model.inline import (
    CodeInline,
    EmphasisInline,
    LineBreakInline,
    StrongInline,
    TextInline,
)
from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.paragraphs import convert_paragraph


def _first_paragraph(html: str) -> ElementNode:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=32)
    html_node = result.root.children[0]
    assert isinstance(html_node, ElementNode)
    body = html_node.children[0]
    assert isinstance(body, ElementNode)
    p = body.children[0]
    assert isinstance(p, ElementNode)
    return p


def test_bold_tag_converts_to_strong_inline() -> None:
    p = _first_paragraph("<p><b>bold</b></p>")

    block, _ = convert_paragraph(p)

    assert block.inlines == (StrongInline(inlines=(TextInline(value="bold"),)),)


def test_strong_tag_converts_to_strong_inline() -> None:
    p = _first_paragraph("<p><strong>bold</strong></p>")

    block, _ = convert_paragraph(p)

    assert block.inlines == (StrongInline(inlines=(TextInline(value="bold"),)),)


def test_italic_tag_converts_to_emphasis_inline() -> None:
    p = _first_paragraph("<p><i>italic</i></p>")

    block, _ = convert_paragraph(p)

    assert block.inlines == (EmphasisInline(inlines=(TextInline(value="italic"),)),)


def test_em_tag_converts_to_emphasis_inline() -> None:
    p = _first_paragraph("<p><em>italic</em></p>")

    block, _ = convert_paragraph(p)

    assert block.inlines == (EmphasisInline(inlines=(TextInline(value="italic"),)),)


def test_code_tag_flattens_nested_text() -> None:
    p = _first_paragraph("<p><code>int <b>main</b>()</code></p>")

    block, _ = convert_paragraph(p)

    assert block.inlines == (CodeInline(value="int main()"),)


def test_empty_code_tag_is_omitted() -> None:
    p = _first_paragraph("<p><code></code>text</p>")

    block, _ = convert_paragraph(p)

    assert block.inlines == (TextInline(value="text"),)


def test_br_tag_converts_to_line_break_inline() -> None:
    p = _first_paragraph("<p>line one<br>line two</p>")

    block, _ = convert_paragraph(p)

    assert block.inlines == (
        TextInline(value="line one"),
        LineBreakInline(),
        TextInline(value="line two"),
    )


def test_nested_bold_inside_italic_preserves_nesting() -> None:
    p = _first_paragraph("<p><i><b>both</b></i></p>")

    block, _ = convert_paragraph(p)

    assert block.inlines == (
        EmphasisInline(inlines=(StrongInline(inlines=(TextInline(value="both"),)),)),
    )


def test_unknown_element_still_recurses_transparently_alongside_known_tags() -> None:
    p = _first_paragraph('<p>a <span class="x"><b>b</b></span> c</p>')

    block, _ = convert_paragraph(p)

    assert block.inlines == (
        TextInline(value="a "),
        StrongInline(inlines=(TextInline(value="b"),)),
        TextInline(value=" c"),
    )
