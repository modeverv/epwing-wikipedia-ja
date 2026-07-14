from __future__ import annotations

from wikiepwing.search.punctuation_variant import punctuation_removed_variant


def test_removes_katakana_middle_dot() -> None:
    assert punctuation_removed_variant("すたー・うぉーず") == "すたーうぉーず"


def test_removes_ascii_punctuation() -> None:
    assert punctuation_removed_variant("rock'n'roll") == "rocknroll"


def test_removes_brackets() -> None:
    assert punctuation_removed_variant("「東京」") == "東京"


def test_removes_japanese_period_and_comma() -> None:
    assert punctuation_removed_variant("あ。い、う") == "あいう"


def test_no_punctuation_returns_none() -> None:
    assert punctuation_removed_variant("emacs") is None
    assert punctuation_removed_variant("東京都") is None


def test_string_that_is_only_punctuation_returns_none() -> None:
    assert punctuation_removed_variant("...") is None


def test_prolonged_sound_mark_is_not_punctuation() -> None:
    # U+30FC is a modifier letter in Unicode's database, not punctuation --
    # it stays, matching wikiepwing.search.kana_variant leaving it alone too.
    assert punctuation_removed_variant("かー") is None
