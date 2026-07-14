from __future__ import annotations

from wikiepwing.search.kana_variant import kana_variant


def test_hiragana_converts_to_katakana() -> None:
    assert kana_variant("ひらがな") == "ヒラガナ"


def test_katakana_converts_to_hiragana() -> None:
    assert kana_variant("カタカナ") == "かたかな"


def test_mixed_kana_swaps_each_character_independently() -> None:
    assert kana_variant("ひらガナ") == "ヒラがな"


def test_kanji_and_ascii_are_left_unchanged() -> None:
    assert kana_variant("東京") is None
    assert kana_variant("emacs") is None


def test_kana_mixed_with_kanji_only_swaps_the_kana_part() -> None:
    assert kana_variant("東京とうきょう") == "東京トウキョウ"


def test_prolonged_sound_mark_has_no_hiragana_equivalent_and_is_unchanged() -> None:
    assert kana_variant("カー") == "かー"
