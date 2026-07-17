from __future__ import annotations

from pathlib import Path

import pytest

from wikiepwing.gaiji.glyph_renderer import (
    GlyphRenderError,
    bitmap_hash,
    render_glyph_bitmap,
    resolve_font_path,
)

# This dev environment has no Debian fonts-noto-cjk package installed (that
# only exists inside docker/toolchain.Dockerfile's image); fall back to a
# CJK-capable font this host actually has so rendering tests still exercise
# real font loading rather than skipping outright everywhere.
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


def test_render_glyph_bitmap_produces_a_valid_png() -> None:
    font_path = _find_cjk_font()
    if font_path is None:
        pytest.skip("no CJK font available in this environment")

    bitmap = render_glyph_bitmap("東", font_path=font_path)

    assert bitmap.startswith(b"\x89PNG\r\n\x1a\n")


def test_render_glyph_bitmap_is_deterministic() -> None:
    font_path = _find_cjk_font()
    if font_path is None:
        pytest.skip("no CJK font available in this environment")

    first = render_glyph_bitmap("葛", font_path=font_path)
    second = render_glyph_bitmap("葛", font_path=font_path)

    assert first == second


def test_different_sequences_render_different_bitmaps() -> None:
    font_path = _find_cjk_font()
    if font_path is None:
        pytest.skip("no CJK font available in this environment")

    a = render_glyph_bitmap("東", font_path=font_path)
    b = render_glyph_bitmap("西", font_path=font_path)

    assert a != b


def test_missing_font_file_raises_glyph_render_error(tmp_path: Path) -> None:
    with pytest.raises(GlyphRenderError, match="cannot load font"):
        render_glyph_bitmap("東", font_path=tmp_path / "no-such-font.ttc")


def test_empty_sequence_raises_glyph_render_error() -> None:
    font_path = _find_cjk_font()
    if font_path is None:
        pytest.skip("no CJK font available in this environment")

    with pytest.raises(GlyphRenderError, match="non-empty"):
        render_glyph_bitmap("", font_path=font_path)


def test_bitmap_hash_is_sha256_hex_digest() -> None:
    digest = bitmap_hash(b"hello")

    assert digest == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert len(digest) == 64


def test_bitmap_hash_is_deterministic() -> None:
    assert bitmap_hash(b"data") == bitmap_hash(b"data")


def test_bitmap_hash_differs_for_different_content() -> None:
    assert bitmap_hash(b"a") != bitmap_hash(b"b")


def test_resolve_font_path_prefers_an_explicit_existing_path(tmp_path: Path) -> None:
    font_file = tmp_path / "custom.ttc"
    font_file.write_bytes(b"not a real font, existence is all that matters here")

    assert resolve_font_path(font_path=font_file) == font_file


def test_resolve_font_path_falls_back_when_explicit_path_is_missing(tmp_path: Path) -> None:
    result = resolve_font_path(font_path=tmp_path / "no-such-font.ttc")

    assert result is None or result.is_file()


def test_resolve_font_path_finds_some_font_in_this_dev_environment() -> None:
    result = resolve_font_path()

    if result is None:
        pytest.skip("no CJK font available in this environment")
    assert result.is_file()
