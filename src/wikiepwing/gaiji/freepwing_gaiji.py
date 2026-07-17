"""FreePWING gaiji build file writer (TASK-M007, ARCHITECTURE.md 17.2/18.3/18.4).

Converts TASK-M005's rendered glyphs and TASK-M006's assigned codes into
the actual input `fpwmake` reads to build a dictionary's external
character (gaiji) fonts: one XBM bitmap file per gaiji, plus a
`halfchars.txt`/`fullchars.txt` line per gaiji naming it and its XBM file
(`tests/fixtures/handcrafted/halfchars.txt`/`fullchars.txt`, exercised
against the real toolchain in TASK-H009's Docker smoke test, is this
module's reference format).

XBM byte packing: `tests/fixtures/handcrafted/generate_gaiji.pl`'s known
byte sequences decode as LSB-first (bit 0 of a byte is the leftmost pixel
of that 8-pixel group) with bit=1 meaning foreground ink -- this module
matches that convention exactly rather than guessing at the XBM spec.
Narrow (half-width) gaiji are 8x16; wide (full-width) gaiji are 16x16,
both matching the real fixture's dimensions.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

_WIDTH_PIXELS = {"narrow": 8, "wide": 16}
_HEIGHT_PIXELS = 16
_LIST_FILENAMES = {"narrow": "halfchars.txt", "wide": "fullchars.txt"}


class FreePwingGaijiError(ValueError):
    """Raised when a gaiji build file cannot be produced."""


@dataclass(frozen=True, slots=True)
class GaijiBuildEntry:
    """One gaiji ready to be written into the FreePWING build tree."""

    sequence: str
    assigned_code: str
    width_class: Literal["narrow", "wide"]
    font_path: Path


def xbm_bytes_from_image(image: Image.Image, name: str) -> bytes:
    """Render a 1-bit PIL image as XBM source text, matching `generate_gaiji.pl`'s format."""
    width, height = image.size
    if width % 8 != 0:
        raise FreePwingGaijiError(f"image width must be a multiple of 8: {width}")
    pixels = image.load()
    if pixels is None:
        raise FreePwingGaijiError("image has no pixel data to load")
    row_bytes = width // 8
    values: list[int] = []
    for y in range(height):
        for byte_index in range(row_bytes):
            byte_value = 0
            for bit in range(8):
                x = byte_index * 8 + bit
                is_ink = pixels[x, y] == 0
                if is_ink:
                    byte_value |= 1 << bit
            values.append(byte_value)

    hex_values = ", ".join(f"0x{value:02x}" for value in values)
    source = (
        f"#define {name}_width {width}\n"
        f"#define {name}_height {height}\n"
        f"static unsigned char {name}_bits[] = {{\n  {hex_values}\n}};\n"
    )
    return source.encode("ascii")


def render_glyph_as_xbm(
    sequence: str, *, font_path: Path, width_class: Literal["narrow", "wide"], name: str
) -> bytes:
    """Rasterize `sequence` at gaiji dimensions and return it as XBM source bytes."""
    width = _WIDTH_PIXELS[width_class]
    height = _HEIGHT_PIXELS
    try:
        font = ImageFont.truetype(str(font_path), height)
    except OSError as error:
        raise FreePwingGaijiError(f"cannot load font {font_path}: {error}") from error

    image = Image.new("1", (width, height), color=1)
    draw = ImageDraw.Draw(image)
    bbox = font.getbbox(sequence)
    left, top = (int(bbox[0]), int(bbox[1])) if bbox is not None else (0, 0)
    draw.text((-left, -top), sequence, font=font, fill=0)
    return xbm_bytes_from_image(image, name)


def write_gaiji_build_files(
    entries: Sequence[GaijiBuildEntry],
    destination_dir: Path,
    *,
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    """Write each entry's XBM file plus halfchars.txt/fullchars.txt into `destination_dir`."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    lines_by_width_class: dict[str, list[str]] = {"narrow": [], "wide": []}
    for index, entry in enumerate(entries, start=1):
        xbm_filename = f"{entry.assigned_code}.xbm"
        xbm_bytes = render_glyph_as_xbm(
            entry.sequence,
            font_path=entry.font_path,
            width_class=entry.width_class,
            name=entry.assigned_code.replace("-", "_"),
        )
        (destination_dir / xbm_filename).write_bytes(xbm_bytes)
        lines_by_width_class[entry.width_class].append(f"{entry.assigned_code} {xbm_filename}")
        if on_progress is not None:
            on_progress(index, len(entries))

    for width_class, filename in _LIST_FILENAMES.items():
        lines = lines_by_width_class[width_class]
        (destination_dir / filename).write_text(
            "".join(f"{line}\n" for line in lines), encoding="utf-8"
        )
