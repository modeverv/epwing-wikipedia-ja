from __future__ import annotations

from wikiepwing.gaiji.representability import (
    is_backend_representable,
    unrepresentable_characters,
)


def test_ascii_letter_is_representable() -> None:
    assert is_backend_representable("A") is True


def test_common_kanji_is_representable() -> None:
    assert is_backend_representable("東") is True


def test_hiragana_is_representable() -> None:
    assert is_backend_representable("あ") is True


def test_fullwidth_katakana_is_representable() -> None:
    assert is_backend_representable("ア") is True


def test_emoji_is_not_representable() -> None:
    assert is_backend_representable("😀") is False


def test_rare_cjk_extension_character_is_not_representable() -> None:
    # U+20000 is in the CJK Unified Ideographs Extension B plane, well
    # outside JIS X 0208's repertoire.
    assert is_backend_representable("\U00020000") is False


def test_unrepresentable_characters_returns_only_the_bad_ones_in_order() -> None:
    text = "東京😀タワー🗼"

    result = unrepresentable_characters(text)

    assert result == ("😀", "🗼")


def test_unrepresentable_characters_returns_empty_for_fully_representable_text() -> None:
    assert unrepresentable_characters("東京タワー") == ()
