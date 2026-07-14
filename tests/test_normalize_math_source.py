from __future__ import annotations

from wikiepwing.normalize.math_node import RawMathNode
from wikiepwing.normalize.math_source import (
    canonicalize_math_source,
    compute_math_cache_key,
)


def test_canonicalize_collapses_internal_whitespace() -> None:
    assert canonicalize_math_source("E  =  mc^2") == "E = mc^2"


def test_canonicalize_strips_leading_and_trailing_whitespace() -> None:
    assert canonicalize_math_source("  E=mc^2  ") == "E=mc^2"


def test_canonicalize_applies_nfc_normalization() -> None:
    import unicodedata

    decomposed = unicodedata.normalize("NFD", "café")

    assert canonicalize_math_source(decomposed) == "café"


def test_cache_key_prefers_tex_source_over_text_alternative() -> None:
    node = RawMathNode(tex_source="E=mc^2", text_alternative="different", is_block=False)

    key = compute_math_cache_key(node)

    assert key == compute_math_cache_key(
        RawMathNode(tex_source="E=mc^2", text_alternative=None, is_block=False)
    )


def test_cache_key_falls_back_to_text_alternative_when_no_tex_source() -> None:
    with_alt = RawMathNode(tex_source=None, text_alternative="E=mc^2", is_block=False)
    with_tex = RawMathNode(tex_source="E=mc^2", text_alternative=None, is_block=False)

    assert compute_math_cache_key(with_alt) == compute_math_cache_key(with_tex)


def test_cache_key_is_none_when_no_source_is_available() -> None:
    node = RawMathNode(tex_source=None, text_alternative=None, is_block=False)

    assert compute_math_cache_key(node) is None


def test_cache_key_is_none_when_source_is_only_whitespace() -> None:
    node = RawMathNode(tex_source="   ", text_alternative=None, is_block=False)

    assert compute_math_cache_key(node) is None


def test_cosmetically_different_sources_produce_the_same_cache_key() -> None:
    spaced = RawMathNode(tex_source="E  =  mc^2", text_alternative=None, is_block=False)
    tight = RawMathNode(tex_source="E = mc^2", text_alternative=None, is_block=False)

    assert compute_math_cache_key(spaced) == compute_math_cache_key(tight)


def test_different_formulas_produce_different_cache_keys() -> None:
    first = RawMathNode(tex_source="E=mc^2", text_alternative=None, is_block=False)
    second = RawMathNode(tex_source="a^2+b^2=c^2", text_alternative=None, is_block=False)

    assert compute_math_cache_key(first) != compute_math_cache_key(second)


def test_cache_key_is_a_sha256_hex_digest() -> None:
    node = RawMathNode(tex_source="E=mc^2", text_alternative=None, is_block=False)

    key = compute_math_cache_key(node)

    assert key is not None
    assert len(key) == 64
    assert all(char in "0123456789abcdef" for char in key)
