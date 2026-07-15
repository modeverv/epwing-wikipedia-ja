"""Raster converter (TASK-O007, ARCHITECTURE.md 15.4/17.3).

Shells out to the ImageMagick CLI (`magick` on ImageMagick 7, `convert`
on the ImageMagick 6 the Docker toolchain image pins) to turn TASK-O005's
validated raster bytes (PNG/JPEG/GIF/WEBP) or TASK-O006's sanitized SVG
into the BMP format the EPWING toolchain expects (matching
`tests/fixtures/handcrafted/generate_bitmap.pl`). SVG rasterization goes
through ImageMagick's `librsvg2-bin` delegate. `docker/toolchain/
imagemagick-policy.xml` locks down the dangerous coders/delegates
(15.4's "ImageMagick delegate制限") at the image level; this module does
not re-implement that restriction, it only invokes the CLI.

Bytes stream through stdin/stdout (`format:-`) rather than temp files,
so nothing this project converts ever touches disk outside the process.
"""

from __future__ import annotations

import shutil
import subprocess

DEFAULT_TIMEOUT_SECONDS = 30.0


class RasterConversionError(RuntimeError):
    """Raised when media bytes cannot be converted to a raster graphic."""


def convert_to_bmp(
    content: bytes,
    *,
    source_format: str,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> bytes:
    """Convert `content` (in `source_format`) to BMP bytes via ImageMagick."""
    if not content:
        raise RasterConversionError("content must not be empty")
    if timeout_seconds <= 0:
        raise RasterConversionError("timeout_seconds must be positive")

    executable = _find_imagemagick_executable()
    input_spec = f"{source_format}:-"
    try:
        result = subprocess.run(
            [executable, input_spec, "bmp:-"],
            input=content,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except OSError as error:
        raise RasterConversionError(f"cannot invoke ImageMagick: {error}") from error
    except subprocess.TimeoutExpired as error:
        raise RasterConversionError(
            f"ImageMagick conversion timed out after {timeout_seconds:g} seconds"
        ) from error

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RasterConversionError(f"ImageMagick conversion failed: {stderr}")
    if not result.stdout:
        raise RasterConversionError("ImageMagick conversion produced no output")
    return result.stdout


def is_imagemagick_available() -> bool:
    """Return whether a usable ImageMagick CLI (`magick` or `convert`) was found."""
    return shutil.which("magick") is not None or shutil.which("convert") is not None


def _find_imagemagick_executable() -> str:
    magick = shutil.which("magick")
    if magick is not None:
        return magick
    convert = shutil.which("convert")
    if convert is not None:
        return convert
    raise RasterConversionError("neither the 'magick' nor 'convert' executable was found")
