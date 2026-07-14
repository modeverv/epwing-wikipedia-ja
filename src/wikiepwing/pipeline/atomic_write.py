"""Atomic file writes (TASK-I004): write-to-temp-then-rename so a crash mid-write
never leaves a partial/truncated file at the destination path.

Used for single-shot stage outputs (e.g. entries.jsonl, stage manifests).
Does not apply to raw.sqlite3/model.sqlite3, which are incrementally updated
across many transactions rather than written once and swapped into place.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_bytes(destination: Path, data: bytes) -> None:
    """Write `data` to `destination` atomically (temp file + fsync + rename)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", delete=False
    )
    try:
        temp_path = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    os.replace(temp_path, destination)


def atomic_write_text(destination: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Write `text` to `destination` atomically (temp file + fsync + rename)."""
    atomic_write_bytes(destination, text.encode(encoding))
