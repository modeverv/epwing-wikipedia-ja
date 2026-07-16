"""Logical build hash (TASK-S002, ARCHITECTURE.md 26.1).

26.1 distinguishes two hash kinds for a packaged build: the *physical*
SHA-256 (the actual archive bytes, which ZIP timestamps and filesystem
iteration order can change even when the content is identical) and the
*logical* hash ("entry/index/graphicのcanonical stream hash"), which
must stay stable across two builds that are content-identical but
differ only in those physical details.

`compute_stream_set_hash` is the generic, order-independent primitive:
given a set of named byte streams, it sorts by name and hashes each with
length-prefixed framing (so `[("ab", b"c")]` and `[("a", b"bc")]` never
collide) rather than simple concatenation. `collect_build_streams`/
`compute_logical_build_hash` apply that primitive to this project's
actual canonical streams: TASK-H010's `entries.jsonl`, TASK-M007's gaiji
build files, and TASK-O011's FreePWING graphics build files. The EB
index binary itself is built by `fpwmake` inside the toolchain
container, not produced directly by this project's Python code, so it
is deliberately out of scope here.

This is a note to future readers: `wikiepwing.model.logical_hash` is a
different, earlier concern (TASK-F008's per-`Article` logical hash) --
same name, unrelated scope. This module's `compute_logical_build_hash`
operates on a whole packaged build, not one article.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path


def compute_stream_set_hash(streams: Iterable[tuple[str, bytes]]) -> str:
    """Return a stable sha256 hex digest over `streams`, independent of input order."""
    hasher = hashlib.sha256()
    for name, content in sorted(streams, key=lambda item: item[0]):
        name_bytes = name.encode("utf-8")
        hasher.update(len(name_bytes).to_bytes(8, "big"))
        hasher.update(name_bytes)
        hasher.update(len(content).to_bytes(8, "big"))
        hasher.update(content)
    return hasher.hexdigest()


def collect_build_streams(
    *,
    entries_jsonl: Path,
    gaiji_dir: Path | None = None,
    graphics_dir: Path | None = None,
) -> tuple[tuple[str, bytes], ...]:
    """Collect `(name, content)` streams for `entries_jsonl` and the optional build directories."""
    streams: list[tuple[str, bytes]] = [("entries.jsonl", entries_jsonl.read_bytes())]
    for prefix, directory in (("gaiji", gaiji_dir), ("graphics", graphics_dir)):
        streams.extend(_directory_streams(prefix, directory))
    return tuple(streams)


def compute_logical_build_hash(
    *,
    entries_jsonl: Path,
    gaiji_dir: Path | None = None,
    graphics_dir: Path | None = None,
) -> str:
    """Return the logical hash over this build's canonical entry/gaiji/graphics streams."""
    streams = collect_build_streams(
        entries_jsonl=entries_jsonl, gaiji_dir=gaiji_dir, graphics_dir=graphics_dir
    )
    return compute_stream_set_hash(streams)


def _directory_streams(prefix: str, directory: Path | None) -> list[tuple[str, bytes]]:
    if directory is None:
        return []
    return [
        (f"{prefix}/{path.relative_to(directory).as_posix()}", path.read_bytes())
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    ]
