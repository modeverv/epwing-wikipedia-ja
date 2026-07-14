from __future__ import annotations

import pytest

from wikiepwing.search.normalize_key import NormalizeKeyError, normalize_index_key


def test_fullwidth_letters_fold_to_lowercase_ascii() -> None:
    # DATA_CONTRACTS.md 8's SearchTerm contract example.
    assert normalize_index_key("Ｅｍａｃｓ") == "emacs"


def test_ascii_uppercase_is_case_folded() -> None:
    assert normalize_index_key("EMACS") == "emacs"


def test_leading_and_trailing_whitespace_is_stripped() -> None:
    assert normalize_index_key("  Emacs  ") == "emacs"


def test_internal_whitespace_runs_collapse_to_one_space() -> None:
    assert normalize_index_key("GNU   Emacs") == "gnu emacs"


def test_fullwidth_space_collapses_like_ascii_space() -> None:
    assert normalize_index_key("GNU　Emacs") == "gnu emacs"


def test_japanese_text_is_preserved() -> None:
    assert normalize_index_key("東京都") == "東京都"


def test_empty_string_raises() -> None:
    with pytest.raises(NormalizeKeyError):
        normalize_index_key("")


def test_whitespace_only_string_raises() -> None:
    with pytest.raises(NormalizeKeyError):
        normalize_index_key("   ")
