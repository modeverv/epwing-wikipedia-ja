"""Math render cache (TASK-N004, ARCHITECTURE.md 15.5/22.3).

A filesystem-backed cache keyed by TASK-N002's content-based
`compute_math_cache_key`, following 15.5's image cache key precedent
(`sha256(canonical_url + requested_width + converter_version +
policy_version)`): the on-disk key folds in `MATH_CACHE_VERSION` too, so
bumping that version (e.g. after a TASK-N003 renderer change that could
produce different bytes for the same source) invalidates every existing
cache entry rather than silently reusing stale renders. `22.3` lists
"math cache" as one of the directories living under the work volume;
this module only implements the cache itself, not that path convention.

A `None` cache key (TASK-N002: no stable source was available) always
bypasses the cache -- there's nothing to key an entry on, so every call
renders fresh.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from wikiepwing.pipeline.atomic_write import atomic_write_bytes

MATH_CACHE_VERSION = 1


class MathCache:
    """A filesystem-backed cache of rendered math images."""

    def __init__(self, cache_dir: Path):
        self._cache_dir = cache_dir

    def get_or_render(
        self, cache_key: str | None, *, image_format: str, render: Callable[[], bytes]
    ) -> bytes:
        """Return the cached image for `cache_key`, rendering and storing it on a miss."""
        if cache_key is None:
            return render()

        path = self._path_for(cache_key, image_format)
        if path.is_file():
            return path.read_bytes()

        image_bytes = render()
        atomic_write_bytes(path, image_bytes)
        return image_bytes

    def _path_for(self, cache_key: str, image_format: str) -> Path:
        versioned = f"{cache_key}:{MATH_CACHE_VERSION}:{image_format}"
        digest = hashlib.sha256(versioned.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.{image_format}"
