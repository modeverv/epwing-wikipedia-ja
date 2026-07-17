"""FreePWING graphics build file writer (TASK-O011, ARCHITECTURE.md 17.2).

Converts TASK-O007's BMP-converted media into the actual input `fpwmake`
reads to build a dictionary's color graphics: one `.bmp` file per
graphic, plus a `cgraphs.txt` line naming it and its BMP file
(`tests/fixtures/handcrafted/cgraphs.txt`, exercised against the real
toolchain by `build_fixture.pl`'s `add_color_graphic_start("wiki-mark")`
/ `add_color_graphic_end()` calls, is this module's reference format --
the same "name -> filename" catalog shape TASK-M007 already established
for gaiji's `halfchars.txt`/`fullchars.txt`).

Wiring an entry's actual `RenderedEntry.graphics` and generating the
matching `add_color_graphic_start`/`add_color_graphic_end` calls in the
FreePWING intermediate JSON/Perl build script is a separate step (as
TASK-M006/M007 separated gaiji code assignment and build-file writing
from the per-entry embedding that uses them); this module only writes
the build files a set of already-decided graphic names/bytes need.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

_CATALOG_FILENAME = "cgraphs.txt"
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


class FreePwingGraphicsError(ValueError):
    """Raised when a graphics build file cannot be produced."""


@dataclass(frozen=True, slots=True)
class GraphicBuildEntry:
    """One graphic ready to be written into the FreePWING build tree."""

    name: str
    bmp_bytes: bytes

    def __post_init__(self) -> None:
        if not _SAFE_NAME.fullmatch(self.name):
            raise FreePwingGraphicsError(
                f"graphic name must match {_SAFE_NAME.pattern}: {self.name!r}"
            )
        if not self.bmp_bytes:
            raise FreePwingGraphicsError(f"graphic {self.name!r} has empty bmp_bytes")


def write_graphics_build_files(
    entries: Sequence[GraphicBuildEntry],
    destination_dir: Path,
    *,
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    """Write each entry's BMP file plus `cgraphs.txt` into `destination_dir`."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if not entries and on_progress is not None:
        on_progress(0, 0)
    for index, entry in enumerate(entries, start=1):
        bmp_filename = f"{entry.name}.bmp"
        (destination_dir / bmp_filename).write_bytes(entry.bmp_bytes)
        lines.append(f"{entry.name} {bmp_filename}")
        if on_progress is not None:
            on_progress(index, len(entries))

    (destination_dir / _CATALOG_FILENAME).write_text(
        "".join(f"{line}\n" for line in lines), encoding="utf-8"
    )
