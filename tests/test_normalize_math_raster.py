from __future__ import annotations

import io

import pytest
from PIL import Image

from wikiepwing.normalize.math_raster import (
    MathRasterError,
    convert_png_to_bmp,
    render_math_to_bmp,
)


def _png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_convert_png_to_bmp_returns_bmp_magic() -> None:
    png_bytes = _png_bytes(Image.new("RGBA", (4, 4), (0, 0, 0, 255)))

    result = convert_png_to_bmp(png_bytes)

    assert result.startswith(b"BM")


def test_convert_png_to_bmp_composites_transparent_pixels_onto_background() -> None:
    png_bytes = _png_bytes(Image.new("RGBA", (2, 2), (10, 20, 30, 0)))

    result = convert_png_to_bmp(png_bytes, background=(200, 150, 100))

    decoded = Image.open(io.BytesIO(result)).convert("RGB")
    assert decoded.getpixel((0, 0)) == (200, 150, 100)


def test_convert_png_to_bmp_preserves_opaque_pixels() -> None:
    png_bytes = _png_bytes(Image.new("RGBA", (2, 2), (11, 22, 33, 255)))

    result = convert_png_to_bmp(png_bytes, background=(200, 150, 100))

    decoded = Image.open(io.BytesIO(result)).convert("RGB")
    assert decoded.getpixel((0, 0)) == (11, 22, 33)


def test_convert_png_to_bmp_rejects_empty_bytes() -> None:
    with pytest.raises(MathRasterError, match="empty"):
        convert_png_to_bmp(b"")


def test_convert_png_to_bmp_rejects_invalid_bytes() -> None:
    with pytest.raises(MathRasterError, match="cannot decode"):
        convert_png_to_bmp(b"not a real png")


def test_render_math_to_bmp_returns_bmp_magic() -> None:
    result = render_math_to_bmp("E=mc^2")

    assert result.startswith(b"BM")


def test_render_math_to_bmp_is_deterministic_for_the_same_formula() -> None:
    first = render_math_to_bmp("E=mc^2")
    second = render_math_to_bmp("E=mc^2")

    assert first == second
