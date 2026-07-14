from __future__ import annotations

from wikiepwing.gaiji.classifier import classify_character


def test_ascii_letter_is_class_a() -> None:
    assert classify_character("A") == "A"


def test_common_kanji_is_class_a() -> None:
    assert classify_character("東") == "A"


def test_substitutable_character_without_table_is_not_b() -> None:
    # Non-breaking space is not backend-representable in EUC-JP and has no
    # substitution table supplied, so it should not be classified B.
    assert classify_character(" ") != "B"


def test_substitutable_character_with_table_is_class_b() -> None:
    substitutions = {" ": " "}

    assert classify_character(" ", substitutions=substitutions) == "B"


def test_backend_representable_character_is_a_even_if_in_substitution_table() -> None:
    substitutions = {"A": "B"}

    assert classify_character("A", substitutions=substitutions) == "A"


def test_rare_but_printable_character_without_substitution_is_class_c() -> None:
    # U+20000 (CJK Extension B) has a real glyph but is outside EUC-JP and
    # has no configured substitution.
    assert classify_character("\U00020000") == "C"


def test_ascii_control_character_is_class_a_since_euc_jp_passes_it_through() -> None:
    # EUC-JP is a superset of ASCII byte values, including C0 controls, so
    # this is technically backend-representable even though it carries no
    # visible glyph -- category A is strictly about encodability, not
    # meaningfulness (ARCHITECTURE.md 18.1 draws no such distinction).
    assert classify_character("\x01") == "A"


def test_c1_control_character_is_class_d() -> None:
    # Unlike C0 controls, C1 controls (U+0080-U+009F) are not valid EUC-JP
    # byte sequences, so this one actually reaches the category-D check.
    assert classify_character("\x81") == "D"


def test_format_character_is_class_d() -> None:
    assert classify_character("﻿") == "D"


def test_unassigned_codepoint_is_class_d() -> None:
    # U+0378 is unassigned in Unicode (general category Cn).
    assert classify_character("͸") == "D"


def test_private_use_character_is_class_d() -> None:
    # U+E000 is the first Private Use Area codepoint (general category Co).
    assert classify_character("") == "D"
