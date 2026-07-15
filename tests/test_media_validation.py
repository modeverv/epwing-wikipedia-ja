from __future__ import annotations

import io

import pytest
from PIL import Image

from wikiepwing.media.validation import MediaValidationError, validate_media_bytes


def _image_bytes(image_format: str, size: tuple[int, int] = (10, 10)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (255, 0, 0)).save(buffer, format=image_format)
    return buffer.getvalue()


def test_recognizes_png_magic_bytes() -> None:
    result = validate_media_bytes(
        _image_bytes("PNG"), declared_content_type=None, max_pixels=10_000
    )

    assert result.detected_format == "png"
    assert result.width == 10
    assert result.height == 10


def test_recognizes_jpeg_magic_bytes() -> None:
    result = validate_media_bytes(
        _image_bytes("JPEG"), declared_content_type=None, max_pixels=10_000
    )

    assert result.detected_format == "jpeg"


def test_recognizes_gif_magic_bytes() -> None:
    result = validate_media_bytes(
        _image_bytes("GIF"), declared_content_type=None, max_pixels=10_000
    )

    assert result.detected_format == "gif"


def test_recognizes_webp_magic_bytes() -> None:
    result = validate_media_bytes(
        _image_bytes("WEBP"), declared_content_type=None, max_pixels=10_000
    )

    assert result.detected_format == "webp"


def test_rejects_unrecognized_magic_bytes() -> None:
    with pytest.raises(MediaValidationError, match="magic bytes"):
        validate_media_bytes(b"not an image", declared_content_type=None, max_pixels=10_000)


def test_declared_content_type_matching_format_is_accepted() -> None:
    result = validate_media_bytes(
        _image_bytes("PNG"), declared_content_type="image/png", max_pixels=10_000
    )

    assert result.detected_format == "png"


def test_declared_content_type_mismatching_format_is_rejected() -> None:
    with pytest.raises(MediaValidationError, match="does not match"):
        validate_media_bytes(
            _image_bytes("PNG"), declared_content_type="image/jpeg", max_pixels=10_000
        )


def test_unknown_declared_content_type_is_rejected() -> None:
    with pytest.raises(MediaValidationError, match="does not match"):
        validate_media_bytes(
            _image_bytes("PNG"), declared_content_type="application/octet-stream", max_pixels=10_000
        )


def test_missing_declared_content_type_skips_that_check() -> None:
    result = validate_media_bytes(
        _image_bytes("PNG"), declared_content_type=None, max_pixels=10_000
    )

    assert result.detected_format == "png"


def test_undecodable_content_with_valid_magic_bytes_is_rejected() -> None:
    truncated = b"\x89PNG\r\n\x1a\n" + b"garbage"

    with pytest.raises(MediaValidationError, match="cannot decode"):
        validate_media_bytes(truncated, declared_content_type=None, max_pixels=10_000)


def test_decoded_pixel_count_over_limit_is_rejected() -> None:
    with pytest.raises(MediaValidationError, match="exceeds"):
        validate_media_bytes(
            _image_bytes("PNG", size=(100, 100)), declared_content_type=None, max_pixels=1_000
        )


def test_decoded_pixel_count_at_limit_is_accepted() -> None:
    result = validate_media_bytes(
        _image_bytes("PNG", size=(10, 10)), declared_content_type=None, max_pixels=100
    )

    assert result.width == 10
    assert result.height == 10


def test_rejects_non_positive_max_pixels() -> None:
    with pytest.raises(MediaValidationError, match="max_pixels"):
        validate_media_bytes(_image_bytes("PNG"), declared_content_type=None, max_pixels=0)
