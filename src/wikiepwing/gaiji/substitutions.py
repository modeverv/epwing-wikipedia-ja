"""Safe character substitutions (TASK-M003, ARCHITECTURE.md 18.2).

18.2 lists meaning-preserving substitutions only ("意味を変える置換は行い
ません"): a non-breaking space becomes a normal space, typographic quotes
become their ASCII/configured equivalent, a variation selector is dropped
(keeping the base glyph it modifies) with a diagnostic, and a combining
sequence is re-evaluated after NFC normalization. The first two are a
simple character-to-character map (`DEFAULT_SUBSTITUTIONS`, also what
TASK-M002's `classify_character` expects as its `substitutions`
argument); the latter two are sequence-level operations a single-character
lookup can't express, so `apply_safe_substitutions` handles a whole
string: NFC-normalize first, then drop variation selectors, then apply
the character map.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping

from wikiepwing.model.diagnostics import Diagnostic

# Left/right single and double typographic quotation marks -> ASCII quotes.
_QUOTE_SUBSTITUTIONS: dict[str, str] = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
}

DEFAULT_SUBSTITUTIONS: dict[str, str] = {
    " ": " ",  # non-breaking space -> normal space
    **_QUOTE_SUBSTITUTIONS,
}

_VARIATION_SELECTOR_RANGES = ((0xFE00, 0xFE0F), (0xE0100, 0xE01EF))


def is_variation_selector(character: str) -> bool:
    """Return whether `character` is a Unicode variation selector."""
    code_point = ord(character)
    return any(start <= code_point <= end for start, end in _VARIATION_SELECTOR_RANGES)


def apply_safe_substitutions(
    text: str, *, substitutions: Mapping[str, str] = DEFAULT_SUBSTITUTIONS
) -> tuple[str, tuple[Diagnostic, ...]]:
    """Apply ARCHITECTURE.md 18.2's substitutions to `text`, plus any diagnostics raised."""
    normalized = unicodedata.normalize("NFC", text)
    diagnostics: list[Diagnostic] = []
    result: list[str] = []
    for character in normalized:
        if is_variation_selector(character):
            diagnostics.append(_variation_selector_diagnostic(character))
            continue
        result.append(substitutions.get(character, character))
    return "".join(result), tuple(diagnostics)


def _variation_selector_diagnostic(character: str) -> Diagnostic:
    return Diagnostic(
        code="CHAR_VARIATION_SELECTOR_DROPPED",
        severity="info",
        stage="gaiji_substitutions",
        page_id=None,
        title=None,
        message=f"dropped variation selector U+{ord(character):04X}, keeping its base glyph",
        source_path=None,
        source_excerpt=None,
        details={"code_point": f"U+{ord(character):04X}"},
    )
