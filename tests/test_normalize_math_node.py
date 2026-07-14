from __future__ import annotations

import pytest

from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.math_node import is_math_node, parse_math_node


def _parse(html: str, tag: str) -> ElementNode:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=20)
    return _find(result.root, tag)


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


def test_recognizes_a_math_element() -> None:
    node = _parse("<math></math>", "math")

    assert is_math_node(node) is True


def test_does_not_recognize_a_non_math_element() -> None:
    node = _parse("<span>x</span>", "span")

    assert is_math_node(node) is False


def test_extracts_tex_source_from_annotation() -> None:
    node = _parse(
        '<math alttext="E=mc^2" display="inline">'
        "<semantics><mrow></mrow>"
        '<annotation encoding="application/x-tex">E=mc^2</annotation>'
        "</semantics></math>",
        "math",
    )

    result = parse_math_node(node)

    assert result.tex_source == "E=mc^2"


def test_extracts_alttext_as_text_alternative() -> None:
    node = _parse('<math alttext="{\\displaystyle E=mc^{2}}"></math>', "math")

    result = parse_math_node(node)

    assert result.text_alternative == "{\\displaystyle E=mc^{2}}"


def test_display_block_sets_is_block_true() -> None:
    node = _parse('<math display="block"></math>', "math")

    result = parse_math_node(node)

    assert result.is_block is True


def test_display_inline_or_missing_sets_is_block_false() -> None:
    inline_node = _parse('<math display="inline"></math>', "math")
    missing_node = _parse("<math></math>", "math")

    assert parse_math_node(inline_node).is_block is False
    assert parse_math_node(missing_node).is_block is False


def test_missing_tex_annotation_yields_none() -> None:
    node = _parse('<math alttext="x"></math>', "math")

    result = parse_math_node(node)

    assert result.tex_source is None


def test_missing_alttext_yields_none() -> None:
    node = _parse("<math></math>", "math")

    result = parse_math_node(node)

    assert result.text_alternative is None


def test_annotation_with_different_encoding_is_ignored() -> None:
    node = _parse(
        '<math><annotation encoding="MathML-Presentation">ignored</annotation></math>', "math"
    )

    result = parse_math_node(node)

    assert result.tex_source is None


def test_annotation_nested_deeper_is_still_found() -> None:
    node = _parse(
        "<math><semantics><mrow><mi>x</mi></mrow>"
        '<annotation encoding="application/x-tex">x</annotation>'
        "</semantics></math>",
        "math",
    )

    result = parse_math_node(node)

    assert result.tex_source == "x"


def test_parse_rejects_non_math_element() -> None:
    node = _parse("<span>x</span>", "span")

    with pytest.raises(ValueError, match="not a math element"):
        parse_math_node(node)
