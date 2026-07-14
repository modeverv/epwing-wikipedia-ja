"""Glyph bitmap renderer (TASK-M005, ARCHITECTURE.md 18.3/18.4).

Rasterizes one gaiji Unicode sequence into a PNG bitmap using a real font
file, so TASK-M004's `gaiji_registry.bitmap_hash` column has something to
record. ARCHITECTURE.md 18.4 requires a "再配布可能なNoto CJK系" font
living inside the Docker toolchain image (`docker/toolchain.Dockerfile`
installs Debian's `fonts-noto-cjk` package) rather than shipping the font
file itself as a build artifact -- this module only reads a font path at
call time and never bundles or downloads one.

`DEFAULT_FONT_PATH` is where Debian's `fonts-noto-cjk` package (pinned in
`docker/toolchain.Dockerfile`) installs its regular-weight CJK font; this
is a documented assumption about that package's layout (no network access
to inspect the actual .deb contents was taken during development), not a
guarantee enforced by this module. Callers running outside that Docker
image (e.g. local development) must pass their own `font_path`.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEFAULT_FONT_PATH = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")


class GlyphRenderError(ValueError):
    """Raised when a glyph cannot be rendered into a bitmap."""


def render_glyph_bitmap(sequence: str, *, font_path: Path, font_size: int = 16) -> bytes:
    """Rasterize `sequence` with the font at `font_path`, returning PNG bytes."""
    if not sequence:
        raise GlyphRenderError("sequence must be a non-empty string")
    try:
        font = ImageFont.truetype(str(font_path), font_size)
    except OSError as error:
        raise GlyphRenderError(f"cannot load font {font_path}: {error}") from error

    bbox = font.getbbox(sequence)
    if bbox is None:
        raise GlyphRenderError(f"font has no renderable glyph for sequence: {sequence!r}")
    left, top, right, bottom = bbox
    width, height = int(right - left), int(bottom - top)
    if width <= 0 or height <= 0:
        raise GlyphRenderError(f"font has no renderable glyph for sequence: {sequence!r}")

    image = Image.new("1", (width, height), color=1)
    draw = ImageDraw.Draw(image)
    draw.text((-left, -top), sequence, font=font, fill=0)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def bitmap_hash(bitmap: bytes) -> str:
    """Return the SHA-256 hex digest of `bitmap` (for `gaiji_registry.bitmap_hash`)."""
    return hashlib.sha256(bitmap).hexdigest()
