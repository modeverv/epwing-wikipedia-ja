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


def test_jis_x_0212_only_kanji_is_not_representable() -> None:
    # U+4E02 ("丂") only encodes as EUC-JP via the SS3 (\x8f) prefix for JIS
    # X 0212 -- Python's and Perl's EUC-JP encoders both accept it, but the
    # real FPWParser rejects any \x8f byte with "invalid character"
    # (TASK-T013, GAIJI.md section 3), so it must not count as
    # backend-representable.
    assert "丂".encode("euc-jp").startswith(b"\x8f")
    assert is_backend_representable("丂") is False


def test_unrepresentable_characters_returns_only_the_bad_ones_in_order() -> None:
    text = "東京😀タワー🗼"

    result = unrepresentable_characters(text)

    assert result == ("😀", "🗼")


def test_unrepresentable_characters_returns_empty_for_fully_representable_text() -> None:
    assert unrepresentable_characters("東京タワー") == ()
