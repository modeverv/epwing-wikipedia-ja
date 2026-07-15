"""Math raster conversion (TASK-N005, ARCHITECTURE.md 15.7 step 4).

TASK-N003's `render_math_to_image` produces a transparent-background PNG,
which is not a format the real FreePWING/EB toolchain accepts as a
graphic (`tests/fixtures/handcrafted/generate_bitmap.pl`, exercised
against the real toolchain, shows the expected shape: a `BM`-prefixed,
24-bit-color Windows BMP with a standard `BITMAPINFOHEADER`). This
module composites the PNG's transparent pixels onto an opaque
background -- matching the paper-colored page a rendered dictionary
entry would show around the formula -- and re-encodes the result as
that BMP format.
"""

from __future__ import annotations

import io
from typing import Literal

from PIL import Image, UnidentifiedImageError

from wikiepwing.normalize.math_renderer import render_math_to_image

RgbColor = tuple[int, int, int]


class MathRasterError(ValueError):
    """Raised when a math image cannot be converted to a raster graphic."""


def convert_png_to_bmp(png_bytes: bytes, *, background: RgbColor = (255, 255, 255)) -> bytes:
    """Composite `png_bytes` onto an opaque `background` and return it as BMP bytes."""
    if not png_bytes:
        raise MathRasterError("png_bytes must not be empty")
    try:
        image = Image.open(io.BytesIO(png_bytes))
        image.load()
    except (UnidentifiedImageError, OSError) as error:
        raise MathRasterError(f"cannot decode png bytes: {error}") from error

    rgba = image.convert("RGBA")
    canvas = Image.new("RGB", rgba.size, background)
    canvas.paste(rgba, mask=rgba.getchannel("A"))

    output = io.BytesIO()
    canvas.save(output, format="BMP")
    return output.getvalue()


def render_math_to_bmp(
    tex_source: str,
    *,
    font_size: int = 16,
    background: RgbColor = (255, 255, 255),
) -> bytes:
    """Render `tex_source` to PNG (TASK-N003) and convert it to BMP for EPWING embedding."""
    image_format: Literal["png"] = "png"
    png_bytes = render_math_to_image(tex_source, image_format=image_format, font_size=font_size)
    return convert_png_to_bmp(png_bytes, background=background)
