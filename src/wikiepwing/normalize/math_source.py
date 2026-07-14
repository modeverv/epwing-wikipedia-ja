"""Canonical math source and cache key (TASK-N002, ARCHITECTURE.md 15.7).

15.7's math handling priority list: "1. テキスト代替を保存" (always kept
on `RawMathNode.text_alternative`, TASK-N001) then "2. TeX sourceがあれば
cache keyに使用". `canonicalize_math_source` collapses source-level
noise (whitespace differences, Unicode composition differences) that
doesn't change what formula is being rendered, so two TeX sources that
differ only cosmetically map to the same cache key -- important once
TASK-N004's math cache exists, so it doesn't re-render (and re-store) the
same formula under two different keys.

When no TeX source is available, `compute_math_cache_key` falls back to
the text alternative; when neither exists, there is nothing stable to key
a cache entry on, so it returns `None` and the caller (TASK-N003 onward)
renders without caching.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from wikiepwing.normalize.math_node import RawMathNode

_WHITESPACE_RUN = re.compile(r"\s+")


def canonicalize_math_source(text: str) -> str:
    """Return `text` with whitespace collapsed and Unicode composition normalized."""
    normalized = unicodedata.normalize("NFC", text)
    return _WHITESPACE_RUN.sub(" ", normalized).strip()


def compute_math_cache_key(node: RawMathNode) -> str | None:
    """Return a stable SHA-256 cache key for `node`, or None if no source is available."""
    source = node.tex_source if node.tex_source is not None else node.text_alternative
    if source is None:
        return None
    canonical = canonicalize_math_source(source)
    if not canonical:
        return None
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
