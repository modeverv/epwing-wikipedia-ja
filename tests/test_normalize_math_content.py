from __future__ import annotations

from wikiepwing.normalize.math_content import resolve_math_source
from wikiepwing.normalize.math_node import RawMathNode


def test_prefers_tex_source_over_text_alternative() -> None:
    node = RawMathNode(tex_source="E=mc^2", text_alternative="alt text", is_block=False)

    result = resolve_math_source(node)

    assert result == ("E=mc^2", "tex")


def test_falls_back_to_text_alternative_when_no_tex_source() -> None:
    node = RawMathNode(tex_source=None, text_alternative="alt text", is_block=False)

    result = resolve_math_source(node)

    assert result == ("alt text", "text_alternative")


def test_canonicalizes_the_chosen_source() -> None:
    node = RawMathNode(tex_source="E =  mc^2  ", text_alternative=None, is_block=False)

    result = resolve_math_source(node)

    assert result == ("E = mc^2", "tex")


def test_returns_none_when_no_source_is_available() -> None:
    node = RawMathNode(tex_source=None, text_alternative=None, is_block=False)

    result = resolve_math_source(node)

    assert result is None


def test_returns_none_when_tex_source_and_text_alternative_are_blank() -> None:
    node = RawMathNode(tex_source="   ", text_alternative="  ", is_block=False)

    result = resolve_math_source(node)

    assert result is None


def test_falls_back_to_text_alternative_when_tex_source_is_blank() -> None:
    node = RawMathNode(tex_source="   ", text_alternative="alt text", is_block=False)

    result = resolve_math_source(node)

    assert result == ("alt text", "text_alternative")
