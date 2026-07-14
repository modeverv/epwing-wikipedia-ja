"""Deterministic zstd compression for raw/model BLOB columns, with bounded sizes."""

from __future__ import annotations

import zstandard

DEFAULT_LEVEL = 6
MIN_LEVEL = 1
MAX_LEVEL = 22
DEFAULT_MAX_INPUT_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_OUTPUT_BYTES = 64 * 1024 * 1024
_ZSTD_CONTENTSIZE_UNKNOWN = (1 << 64) - 1
_ZSTD_CONTENTSIZE_ERROR = (1 << 64) - 2


class ZstdCodecError(ValueError):
    """Raised when zstd compression or decompression cannot proceed safely."""


def compress(
    data: bytes,
    *,
    level: int = DEFAULT_LEVEL,
    max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES,
) -> bytes:
    """Compress `data` deterministically at a fixed level, single-threaded."""
    if not MIN_LEVEL <= level <= MAX_LEVEL:
        raise ZstdCodecError(f"level must be between {MIN_LEVEL} and {MAX_LEVEL}: {level}")
    if max_input_bytes < 1:
        raise ZstdCodecError("max_input_bytes must be positive")
    if len(data) > max_input_bytes:
        raise ZstdCodecError(f"input exceeded {max_input_bytes} bytes: {len(data)}")
    compressor = zstandard.ZstdCompressor(level=level, threads=0)
    return compressor.compress(data)


def decompress(
    blob: bytes,
    *,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> bytes:
    """Decompress `blob`, rejecting frames whose declared or actual size is too large."""
    if max_output_bytes < 1:
        raise ZstdCodecError("max_output_bytes must be positive")
    try:
        params = zstandard.get_frame_parameters(blob)
    except zstandard.ZstdError as error:
        raise ZstdCodecError(f"invalid zstd frame: {error}") from error
    declared_size = params.content_size
    if declared_size not in (None, _ZSTD_CONTENTSIZE_UNKNOWN, _ZSTD_CONTENTSIZE_ERROR):
        if declared_size > max_output_bytes:
            raise ZstdCodecError(
                f"declared decompressed size {declared_size} exceeds {max_output_bytes} bytes"
            )
    decompressor = zstandard.ZstdDecompressor()
    try:
        result = decompressor.decompress(blob, max_output_size=max_output_bytes)
    except zstandard.ZstdError as error:
        raise ZstdCodecError(f"cannot decompress zstd frame: {error}") from error
    if len(result) > max_output_bytes:
        raise ZstdCodecError(
            f"decompressed output exceeded {max_output_bytes} bytes: {len(result)}"
        )
    return result
