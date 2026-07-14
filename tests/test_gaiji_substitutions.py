from __future__ import annotations

from wikiepwing.gaiji.substitutions import (
    DEFAULT_SUBSTITUTIONS,
    apply_safe_substitutions,
    is_variation_selector,
)


def test_non_breaking_space_becomes_normal_space() -> None:
    result, diagnostics = apply_safe_substitutions("a b")

    assert result == "a b"
    assert diagnostics == ()


def test_typographic_quotes_become_ascii_quotes() -> None:
    result, _ = apply_safe_substitutions("‘hello’ “world”")

    assert result == "'hello' \"world\""


def test_is_variation_selector_recognizes_standard_range() -> None:
    assert is_variation_selector("️") is True


def test_is_variation_selector_recognizes_supplementary_range() -> None:
    assert is_variation_selector("\U000e0100") is True


def test_is_variation_selector_rejects_ordinary_character() -> None:
    assert is_variation_selector("A") is False


def test_variation_selector_is_dropped_keeping_base_glyph() -> None:
    # U+845B (葛) + U+FE00 (a variation selector requesting a glyph variant).
    result, diagnostics = apply_safe_substitutions("葛︀")

    assert result == "葛"
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CHAR_VARIATION_SELECTOR_DROPPED"


def test_combining_sequence_is_nfc_normalized() -> None:
    import unicodedata

    composed = "ゔ"  # ゔ, precomposed
    decomposed = unicodedata.normalize("NFD", composed)
    assert decomposed != composed  # sanity check that decomposition actually split it

    result, _ = apply_safe_substitutions(decomposed)

    assert result == composed


def test_no_substitution_needed_returns_text_unchanged() -> None:
    result, diagnostics = apply_safe_substitutions("東京タワー")

    assert result == "東京タワー"
    assert diagnostics == ()


def test_custom_substitution_table_is_honored() -> None:
    result, _ = apply_safe_substitutions("x", substitutions={"x": "y"})

    assert result == "y"


def test_default_substitutions_covers_nbsp_and_quotes() -> None:
    assert DEFAULT_SUBSTITUTIONS[" "] == " "
    assert DEFAULT_SUBSTITUTIONS["‘"] == "'"
    assert DEFAULT_SUBSTITUTIONS["’"] == "'"
    assert DEFAULT_SUBSTITUTIONS["“"] == '"'
    assert DEFAULT_SUBSTITUTIONS["”"] == '"'
