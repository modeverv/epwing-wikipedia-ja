"""Punctuation-removed search variant (TASK-J004, ARCHITECTURE.md 14 "punctuation variants").

Users often omit punctuation when searching -- the katakana middle dot
"・" in a compound word, brackets, dashes, Japanese periods and commas.
`normalize_index_key` (TASK-J001) does not remove any of these; NFKC only
folds width/compatibility forms, and case-fold only affects letters. This
mirrors TASK-J002's space-removed variant: strip every character Unicode
classifies as punctuation (`unicodedata.category` starting with "P" --
connector, dash, open/close, initial/final quote, and other punctuation)
so a query typed without punctuation still matches.
"""

from __future__ import annotations

import unicodedata


def punctuation_removed_variant(normalized_key: str) -> str | None:
    """Return `normalized_key` with all punctuation removed, or None if unchanged."""
    without_punctuation = "".join(
        character
        for character in normalized_key
        if not unicodedata.category(character).startswith("P")
    )
    if not without_punctuation or without_punctuation == normalized_key:
        return None
    return without_punctuation
