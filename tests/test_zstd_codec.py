from __future__ import annotations

import pytest
import zstandard

from wikiepwing.ingest.zstd_codec import ZstdCodecError, compress, decompress


def test_roundtrip_returns_original_bytes() -> None:
    original = "Emacsについての説明です。" * 100
    data = original.encode("utf-8")

    blob = compress(data)
    restored = decompress(blob)

    assert restored == data


def test_compress_is_deterministic_for_same_input_and_level() -> None:
    data = b"deterministic content" * 50

    first = compress(data, level=6)
    second = compress(data, level=6)

    assert first == second


def test_different_levels_may_produce_different_bytes_but_both_roundtrip() -> None:
    data = b"level comparison content" * 50

    low = compress(data, level=1)
    high = compress(data, level=19)

    assert decompress(low) == data
    assert decompress(high) == data


def test_empty_input_roundtrips() -> None:
    blob = compress(b"")

    assert decompress(blob) == b""


def test_level_below_minimum_is_rejected() -> None:
    with pytest.raises(ZstdCodecError, match="level"):
        compress(b"data", level=0)


def test_level_above_maximum_is_rejected() -> None:
    with pytest.raises(ZstdCodecError, match="level"):
        compress(b"data", level=23)


def test_oversized_input_is_rejected() -> None:
    with pytest.raises(ZstdCodecError, match="exceeded"):
        compress(b"x" * 100, max_input_bytes=10)


def test_non_positive_max_input_bytes_is_rejected() -> None:
    with pytest.raises(ZstdCodecError, match="max_input_bytes"):
        compress(b"data", max_input_bytes=0)


def test_non_positive_max_output_bytes_is_rejected() -> None:
    blob = compress(b"data")

    with pytest.raises(ZstdCodecError, match="max_output_bytes"):
        decompress(blob, max_output_bytes=0)


def test_invalid_frame_is_rejected() -> None:
    with pytest.raises(ZstdCodecError, match="invalid zstd frame"):
        decompress(b"not a zstd frame at all")


def test_declared_content_size_over_limit_is_rejected_without_decompressing() -> None:
    large_data = b"y" * 10_000
    blob = zstandard.ZstdCompressor(level=1).compress(large_data)

    with pytest.raises(ZstdCodecError, match="declared decompressed size"):
        decompress(blob, max_output_bytes=100)


def test_streaming_frame_without_content_size_is_bounded_during_decompression() -> None:
    large_data = b"z" * 10_000
    compressor = zstandard.ZstdCompressor(level=1, write_content_size=False)
    blob = compressor.compress(large_data)

    with pytest.raises(ZstdCodecError, match="cannot decompress"):
        decompress(blob, max_output_bytes=100)
