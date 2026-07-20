"""Unicode character classifier (TASK-M002, ARCHITECTURE.md 18.1).

Classifies one Unicode scalar into 18.1's four output categories:

- `"A"`: backend-representable as-is (TASK-M001's `is_backend_representable`).
- `"B"`: not backend-representable, but a configured safe substitution
  exists for it (TASK-M003 builds the real substitution table; this
  classifier only calls it, taking `substitutions` as a parameter so it
  does not need to exist yet).
- `"C"`: not A or B, but the character still has a meaningful glyph a
  gaiji bitmap (TASK-M004 onward) could represent.
- `"D"`: unrepresentable outright -- Unicode general categories Cc
  (control), Cf (format), Cs (surrogate), Co (private use), and Cn
  (unassigned) have no glyph worth rendering as a bitmap at all
  (ARCHITECTURE.md 18.5's fallback is a codepoint marker, not a bitmap).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from typing import Literal

from wikiepwing.gaiji.representability import is_backend_representable

CharacterClass = Literal["A", "B", "C", "D"]

_NO_GLYPH_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Cn"})


def classify_character(
    character: str, *, substitutions: Mapping[str, str] | None = None
) -> CharacterClass:
    """Classify one Unicode scalar per ARCHITECTURE.md 18.1."""
    if character in {"\x1e", "\x1f"}:
        return "A"
    if is_backend_representable(character):
        return "A"
    if substitutions is not None and character in substitutions:
        return "B"
    if unicodedata.category(character) in _NO_GLYPH_CATEGORIES:
        return "D"
    return "C"
