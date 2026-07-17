"""Backend representability table (TASK-M001, ARCHITECTURE.md 18.1 category A).

A character is a "backend標準文字" (ARCHITECTURE.md 18.1 category A) when
the EPWING/FreePWING toolchain can carry it through unchanged.
`wikiepwing.render.freepwing_source` already established (TASK-H009) that
every string reaching `FreePWING::FPWUtils::FPWParser` must first be
encoded as EUC-JP -- but Python's own `codecs` EUC-JP implementation is
*not* the real toolchain's representability table by itself (GAIJI.md
section 3): it happily encodes JIS X 0212 supplementary kanji using the
SS3 prefix byte (`\\x8f`), and so does Perl's `Encode` module (confirmed
against the real toolchain), but `FreePWING::FPWUtils::FPWParser` itself
does not understand SS3 and rejects any `\\x8f` byte with "invalid
character" (TASK-T013). So a character only counts as backend-representable
here when it encodes as EUC-JP *and* that encoding doesn't start with the
SS3 prefix -- this matches the real toolchain's accepted repertoire (ASCII,
JIS X 0201 kana, plain two-byte JIS X 0208 kanji/kana/symbols) exactly.

TASK-M002's classifier (categories B/C/D for whatever this module rejects)
builds on top of this.
"""

from __future__ import annotations

_BACKEND_ENCODING = "euc-jp"
_JIS_X_0212_SS3_PREFIX = b"\x8f"


def is_backend_representable(character: str) -> bool:
    """Return whether `character` (a single Unicode scalar) survives EUC-JP encoding.

    A JIS X 0212-only character (SS3, `\\x8f` prefix) technically encodes as
    EUC-JP but is rejected by the real `FPWParser`, so it does not count as
    backend-representable here.
    """
    try:
        encoded = character.encode(_BACKEND_ENCODING)
    except UnicodeEncodeError:
        return False
    return not encoded.startswith(_JIS_X_0212_SS3_PREFIX)


def unrepresentable_characters(text: str) -> tuple[str, ...]:
    """Return every character in `text` that is not backend-representable, in order."""
    return tuple(character for character in text if not is_backend_representable(character))
