from __future__ import annotations

from wikiepwing.search.space_variant import space_removed_variant


def test_returns_space_removed_form_when_key_has_internal_space() -> None:
    assert space_removed_variant("new york") == "newyork"


def test_returns_none_when_key_has_no_whitespace() -> None:
    assert space_removed_variant("emacs") is None


def test_removes_multiple_internal_spaces() -> None:
    assert space_removed_variant("gnu emacs lisp") == "gnuemacslisp"


def test_removes_non_ascii_whitespace_too() -> None:
    assert space_removed_variant("gnu　emacs") == "gnuemacs"
