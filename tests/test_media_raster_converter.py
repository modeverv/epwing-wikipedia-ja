from __future__ import annotations

import io

import pytest
from PIL import Image

from wikiepwing.media import raster_converter
from wikiepwing.media.raster_converter import (
    RasterConversionError,
    convert_to_bmp,
    is_imagemagick_available,
)

_requires_imagemagick = pytest.mark.skipif(
    not is_imagemagick_available(),
    reason="ImageMagick (magick/convert) is not installed in this environment",
)


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), (255, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


@_requires_imagemagick
def test_converts_png_to_bmp() -> None:
    result = convert_to_bmp(_png_bytes(), source_format="png")

    assert result.startswith(b"BM")


@_requires_imagemagick
def test_converts_svg_to_bmp() -> None:
    svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        b'<rect width="10" height="10" fill="red"/></svg>'
    )

    result = convert_to_bmp(svg, source_format="svg")

    assert result.startswith(b"BM")


@_requires_imagemagick
def test_invalid_content_raises_conversion_error() -> None:
    with pytest.raises(RasterConversionError, match="failed"):
        convert_to_bmp(b"not a real image", source_format="png")


def test_rejects_empty_content() -> None:
    with pytest.raises(RasterConversionError, match="empty"):
        convert_to_bmp(b"", source_format="png")


def test_rejects_non_positive_timeout() -> None:
    with pytest.raises(RasterConversionError, match="timeout_seconds"):
        convert_to_bmp(b"content", source_format="png", timeout_seconds=0)


def test_missing_executable_raises_conversion_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(raster_converter.shutil, "which", lambda _name: None)

    with pytest.raises(RasterConversionError, match="magick"):
        convert_to_bmp(b"content", source_format="png")


def test_is_imagemagick_available_reflects_which_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(raster_converter.shutil, "which", lambda _name: None)

    assert is_imagemagick_available() is False
