"""MIME/magic-byte and decoded-pixel validation (TASK-O005, ARCHITECTURE.md 15.4).

Covers 15.4's "MIMEとmagic byte検証" and "実デコード後pixel上限":
`validate_media_bytes` sniffs the real format from the file's own magic
bytes (never trusting a server-supplied `Content-Type` on its own),
cross-checks that header against the declared `Content-Type` when one is
present, decodes the image with Pillow to get its *actual* dimensions
(a mismatched or lying `Content-Length`/header claim doesn't change what
the pixels actually are), and rejects anything whose decoded pixel count
exceeds a caller-supplied limit -- guarding against a decompression-bomb
image that is small on disk but enormous once decoded.

SVG is XML, not a fixed-magic-byte raster format, and carries its own
threat model (external entities, embedded scripts); it is deliberately
out of scope here and handled by TASK-O006's SVG sanitizer instead.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

_MAGIC_SIGNATURES: tuple[tuple[str, bytes], ...] = (
    ("png", b"\x89PNG\r\n\x1a\n"),
    ("jpeg", b"\xff\xd8\xff"),
    ("gif", b"GIF87a"),
    ("gif", b"GIF89a"),
)
_CONTENT_TYPE_FORMATS: dict[str, frozenset[str]] = {
    "image/png": frozenset({"png"}),
    "image/jpeg": frozenset({"jpeg"}),
    "image/jpg": frozenset({"jpeg"}),
    "image/gif": frozenset({"gif"}),
    "image/webp": frozenset({"webp"}),
}


class MediaValidationError(ValueError):
    """Raised when media bytes fail MIME/magic-byte or decoded-pixel validation."""


@dataclass(frozen=True, slots=True)
class MediaValidationResult:
    """The verified shape of one validated media file."""

    detected_format: str
    width: int
    height: int


def validate_media_bytes(
    content: bytes,
    *,
    declared_content_type: str | None,
    max_pixels: int,
) -> MediaValidationResult:
    """Validate `content` against magic bytes, `declared_content_type`, and `max_pixels`."""
    if max_pixels < 1:
        raise MediaValidationError("max_pixels must be positive")

    detected_format = _sniff_format(content)
    if detected_format is None:
        raise MediaValidationError("content does not match any recognized image magic bytes")

    if declared_content_type is not None:
        allowed_formats = _CONTENT_TYPE_FORMATS.get(declared_content_type.lower())
        if allowed_formats is None or detected_format not in allowed_formats:
            raise MediaValidationError(
                f"declared Content-Type {declared_content_type!r} does not match "
                f"detected format {detected_format!r}"
            )

    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError) as error:
        raise MediaValidationError(f"cannot decode image content: {error}") from error

    width, height = image.size
    if width * height > max_pixels:
        raise MediaValidationError(
            f"decoded pixel count {width * height} exceeds the {max_pixels}-pixel limit"
        )

    return MediaValidationResult(detected_format=detected_format, width=width, height=height)


def _sniff_format(content: bytes) -> str | None:
    for name, signature in _MAGIC_SIGNATURES:
        if content.startswith(signature):
            return name
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None
