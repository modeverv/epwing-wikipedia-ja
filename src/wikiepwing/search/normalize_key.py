"""Search index key normalization contract (TASK-J001, DATA_CONTRACTS.md 8 "SearchTerm contract").

`normalize_index_key` is the single normalization function every SearchTerm's
`normalized_key` must be derived from. DATA_CONTRACTS.md 8's example maps
`"Ｅｍａｃｓ"` (full-width) to `"emacs"`: NFKC folds full-width letters to
their half-width ASCII form, and Unicode case-folding (not just `.lower()`)
then collapses case. This is deliberately distinct from
`wikiepwing.ingest.repository.normalize_title`, which normalizes titles for
raw-ingest deduplication (NFKC + strip only, case-preserving) -- a separate
concern this task leaves untouched.

NFKC/case/space variants (TASK-J002), kana variants (TASK-J003), and
punctuation variants (TASK-J004) build additional SearchTerm variants on top
of this baseline; they are not this task's scope.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RUN = re.compile(r"\s+")


class NormalizeKeyError(ValueError):
    """Raised when a search index key cannot be normalized safely."""


def normalize_index_key(text: str) -> str:
    """Return `text` normalized into a search index key (NFKC, case-folded, trimmed)."""
    folded = unicodedata.normalize("NFKC", text).casefold()
    collapsed = _WHITESPACE_RUN.sub(" ", folded).strip()
    if not collapsed:
        raise NormalizeKeyError(f"text normalizes to an empty index key: {text!r}")
    return collapsed
