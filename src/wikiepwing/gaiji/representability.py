"""Backend representability table (TASK-M001, ARCHITECTURE.md 18.1 category A).

A character is a "backend標準文字" (ARCHITECTURE.md 18.1 category A) when
the EPWING/FreePWING toolchain can carry it through unchanged.
`wikiepwing.render.freepwing_source` already established (TASK-H009) that
every string reaching `FreePWING::FPWUtils::FPWParser` must first be
encoded as EUC-JP -- that toolchain fact *is* this project's backend
representability table, so this module doesn't reimplement a Unicode
coverage table; it asks Python's own `codecs` EUC-JP implementation,
which already encodes exactly the character repertoire (ASCII, JIS X
0201 kana, JIS X 0208 kanji/kana/symbols) the real toolchain accepts.

TASK-M002's classifier (categories B/C/D for whatever this module rejects)
builds on top of this.
"""

from __future__ import annotations

_BACKEND_ENCODING = "euc-jp"


def is_backend_representable(character: str) -> bool:
    """Return whether `character` (a single Unicode scalar) survives EUC-JP encoding."""
    try:
        character.encode(_BACKEND_ENCODING)
    except UnicodeEncodeError:
        return False
    return True


def unrepresentable_characters(text: str) -> tuple[str, ...]:
    """Return every character in `text` that is not backend-representable, in order."""
    return tuple(character for character in text if not is_backend_representable(character))
