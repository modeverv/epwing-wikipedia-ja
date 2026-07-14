from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from wikiepwing.gaiji.freepwing_gaiji import (
    FreePwingGaijiError,
    GaijiBuildEntry,
    render_glyph_as_xbm,
    write_gaiji_build_files,
    xbm_bytes_from_image,
)

_CANDIDATE_FONT_PATHS = (
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
)


def _find_cjk_font() -> Path | None:
    for candidate in _CANDIDATE_FONT_PATHS:
        if candidate.is_file():
            return candidate
    return None


# The real fixture (tests/fixtures/handcrafted/generate_gaiji.pl) writes this
# exact byte sequence for its "half" 8x16 bowtie/hourglass test pattern; we
# rebuild the same pixels from a PIL image and confirm we reproduce it
# byte-for-byte, proving our LSB-first/ink=1 packing convention matches.
_HALF_BITS = [
    0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81,
    0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81,
]  # fmt: skip


def _image_from_bits(width: int, height: int, byte_rows: list[int]) -> Image.Image:
    image = Image.new("1", (width, height), color=1)
    pixels = image.load()
    row_bytes = width // 8
    for y in range(height):
        for byte_index in range(row_bytes):
            byte_value = byte_rows[y * row_bytes + byte_index]
            for bit in range(8):
                x = byte_index * 8 + bit
                is_ink = bool(byte_value & (1 << bit))
                pixels[x, y] = 0 if is_ink else 1
    return image


def test_xbm_bytes_from_image_matches_the_real_fixture_pattern() -> None:
    image = _image_from_bits(8, 16, _HALF_BITS)

    result = xbm_bytes_from_image(image, "half")

    hex_values = ", ".join(f"0x{value:02x}" for value in _HALF_BITS)
    expected = (
        "#define half_width 8\n"
        "#define half_height 16\n"
        f"static unsigned char half_bits[] = {{\n  {hex_values}\n}};\n"
    ).encode("ascii")
    assert result == expected


def test_xbm_bytes_from_image_rejects_non_multiple_of_8_width() -> None:
    image = Image.new("1", (10, 16), color=1)

    with pytest.raises(FreePwingGaijiError, match="multiple of 8"):
        xbm_bytes_from_image(image, "bad")


def test_all_white_image_produces_all_zero_bytes() -> None:
    image = Image.new("1", (8, 16), color=1)

    result = xbm_bytes_from_image(image, "blank")

    assert "0x00, 0x00" in result.decode("ascii")


def test_render_glyph_as_xbm_produces_narrow_dimensions() -> None:
    font_path = _find_cjk_font()
    if font_path is None:
        pytest.skip("no CJK font available in this environment")

    result = render_glyph_as_xbm("葛", font_path=font_path, width_class="narrow", name="test")

    assert b"test_width 8" in result
    assert b"test_height 16" in result


def test_render_glyph_as_xbm_produces_wide_dimensions() -> None:
    font_path = _find_cjk_font()
    if font_path is None:
        pytest.skip("no CJK font available in this environment")

    result = render_glyph_as_xbm("葛", font_path=font_path, width_class="wide", name="test")

    assert b"test_width 16" in result
    assert b"test_height 16" in result


def test_write_gaiji_build_files_writes_xbm_and_list_files(tmp_path: Path) -> None:
    font_path = _find_cjk_font()
    if font_path is None:
        pytest.skip("no CJK font available in this environment")

    entries = [
        GaijiBuildEntry(
            sequence="葛", assigned_code="narrow-0001", width_class="narrow", font_path=font_path
        ),
        GaijiBuildEntry(
            sequence="蔦", assigned_code="wide-0001", width_class="wide", font_path=font_path
        ),
    ]

    write_gaiji_build_files(entries, tmp_path)

    assert (tmp_path / "narrow-0001.xbm").is_file()
    assert (tmp_path / "wide-0001.xbm").is_file()
    assert (tmp_path / "halfchars.txt").read_text(
        encoding="utf-8"
    ) == "narrow-0001 narrow-0001.xbm\n"
    assert (tmp_path / "fullchars.txt").read_text(encoding="utf-8") == "wide-0001 wide-0001.xbm\n"


def test_write_gaiji_build_files_with_no_entries_writes_empty_list_files(tmp_path: Path) -> None:
    write_gaiji_build_files([], tmp_path)

    assert (tmp_path / "halfchars.txt").read_text(encoding="utf-8") == ""
    assert (tmp_path / "fullchars.txt").read_text(encoding="utf-8") == ""
