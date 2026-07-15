"""Content-addressed media cache (TASK-O008, ARCHITECTURE.md 15.5).

A filesystem-backed cache keyed by the sha256 of the *downloaded* bytes
themselves (`compute_content_hash`), not a derived formula like TASK-N004's
math cache -- so two different `MediaReference.source_url`s that happen
to point at byte-identical files land in the same cache entry, without
either caller needing to know about the other. That sharing is exactly
what TASK-O009's dedup builds on.

`MEDIA_CACHE_VERSION` is folded into the on-disk key, following 15.5's
`converter_version` precedent: bumping it (e.g. after a TASK-O007 raster
conversion change that could produce different bytes for the same
source) invalidates every existing cache entry instead of silently
reusing a stale conversion.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from wikiepwing.pipeline.atomic_write import atomic_write_bytes

MEDIA_CACHE_VERSION = 1


def compute_content_hash(content: bytes) -> str:
    """Return the sha256 hex digest of `content`, used as its cache key."""
    return hashlib.sha256(content).hexdigest()


class MediaCache:
    """A filesystem-backed cache of converted media, keyed by content hash."""

    def __init__(self, cache_dir: Path):
        self._cache_dir = cache_dir

    def get_or_convert(self, content_hash: str, *, convert: Callable[[], bytes]) -> bytes:
        """Return the cached conversion for `content_hash`, converting and storing it on a miss."""
        path = self._path_for(content_hash)
        if path.is_file():
            return path.read_bytes()

        converted = convert()
        atomic_write_bytes(path, converted)
        return converted

    def _path_for(self, content_hash: str) -> Path:
        versioned = f"{content_hash}:{MEDIA_CACHE_VERSION}"
        digest = hashlib.sha256(versioned.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.bmp"
