"""Hiragana/katakana search variant (TASK-J003, ARCHITECTURE.md 14.3 "kana variant").

Swaps every hiragana character to its katakana equivalent and every
katakana character to its hiragana equivalent, leaving everything else
unchanged, so a title/alias written in one kana script is still found by a
query typed in the other. Half-width katakana is not handled here: NFKC
normalization (TASK-J001's `normalize_index_key`) already folds half-width
katakana to full-width before this function ever sees the string.
"""

from __future__ import annotations

_HIRAGANA_START = 0x3041  # ぁ
_HIRAGANA_END = 0x3096  # ゖ
_KATAKANA_START = 0x30A1  # ァ
_KATAKANA_END = 0x30F6  # ヶ
_HIRAGANA_TO_KATAKANA_OFFSET = 0x60


def kana_variant(normalized_key: str) -> str | None:
    """Return `normalized_key` with hiragana/katakana swapped, or None if unchanged."""
    swapped_chars = [_swap_kana(character) for character in normalized_key]
    swapped = "".join(swapped_chars)
    if swapped == normalized_key:
        return None
    return swapped


def _swap_kana(character: str) -> str:
    code_point = ord(character)
    if _HIRAGANA_START <= code_point <= _HIRAGANA_END:
        return chr(code_point + _HIRAGANA_TO_KATAKANA_OFFSET)
    if _KATAKANA_START <= code_point <= _KATAKANA_END:
        return chr(code_point - _HIRAGANA_TO_KATAKANA_OFFSET)
    return character
