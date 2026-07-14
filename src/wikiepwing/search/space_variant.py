"""Space-removed search variant (TASK-J002, ARCHITECTURE.md 14 "NFKC/case/space variants").

NFKC and case differences (full-width vs half-width, uppercase vs
lowercase) do not need a separately stored SearchTerm: `normalize_index_key`
(TASK-J001) folds both a stored key and an incoming query through the same
NFKC + case-fold pipeline, so "Ｅｍａｃｓ" and "emacs" already converge on
one `normalized_key` regardless of which one a user types (this requires
the backend to apply `normalize_index_key` to queries too -- TASK-J007's
job, not this one).

Whitespace does not converge the same way: `normalize_index_key` only
collapses whitespace *runs* down to one space, it never removes a space
outright. "New York" (one space) and "NewYork" (no space) stay distinct
strings after normalization. `space_removed_variant` produces the
space-removed form so callers can register it as an extra alias
SearchTerm, letting users find a multi-word title whether or not they
typed the space.
"""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def space_removed_variant(normalized_key: str) -> str | None:
    """Return `normalized_key` with all whitespace removed, or None if unchanged."""
    without_space = _WHITESPACE.sub("", normalized_key)
    if without_space == normalized_key:
        return None
    return without_space
