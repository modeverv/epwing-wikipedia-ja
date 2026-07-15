from __future__ import annotations

from pathlib import Path

import pytest

from wikiepwing.media.freepwing_graphics import (
    FreePwingGraphicsError,
    GraphicBuildEntry,
    write_graphics_build_files,
)


def test_write_graphics_build_files_writes_bmp_and_catalog(tmp_path: Path) -> None:
    entries = [
        GraphicBuildEntry(name="wiki-mark", bmp_bytes=b"BMfakebytes1"),
        GraphicBuildEntry(name="lead-image", bmp_bytes=b"BMfakebytes2"),
    ]

    write_graphics_build_files(entries, tmp_path)

    assert (tmp_path / "wiki-mark.bmp").read_bytes() == b"BMfakebytes1"
    assert (tmp_path / "lead-image.bmp").read_bytes() == b"BMfakebytes2"
    assert (tmp_path / "cgraphs.txt").read_text(encoding="utf-8") == (
        "wiki-mark wiki-mark.bmp\nlead-image lead-image.bmp\n"
    )


def test_write_graphics_build_files_with_no_entries_writes_empty_catalog(tmp_path: Path) -> None:
    write_graphics_build_files([], tmp_path)

    assert (tmp_path / "cgraphs.txt").read_text(encoding="utf-8") == ""


def test_write_graphics_build_files_creates_missing_directory(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "graphics"
    entries = [GraphicBuildEntry(name="wiki-mark", bmp_bytes=b"BMfakebytes")]

    write_graphics_build_files(entries, destination)

    assert (destination / "wiki-mark.bmp").is_file()


def test_write_graphics_build_files_preserves_input_order(tmp_path: Path) -> None:
    entries = [
        GraphicBuildEntry(name="z-graphic", bmp_bytes=b"BMz"),
        GraphicBuildEntry(name="a-graphic", bmp_bytes=b"BMa"),
    ]

    write_graphics_build_files(entries, tmp_path)

    lines = (tmp_path / "cgraphs.txt").read_text(encoding="utf-8").splitlines()
    assert lines == ["z-graphic z-graphic.bmp", "a-graphic a-graphic.bmp"]


def test_rejects_empty_name() -> None:
    with pytest.raises(FreePwingGraphicsError, match="graphic name"):
        GraphicBuildEntry(name="", bmp_bytes=b"BM")


def test_rejects_name_with_whitespace() -> None:
    with pytest.raises(FreePwingGraphicsError, match="graphic name"):
        GraphicBuildEntry(name="has space", bmp_bytes=b"BM")


def test_rejects_name_with_newline() -> None:
    with pytest.raises(FreePwingGraphicsError, match="graphic name"):
        GraphicBuildEntry(name="bad\nname", bmp_bytes=b"BM")


def test_rejects_empty_bmp_bytes() -> None:
    with pytest.raises(FreePwingGraphicsError, match="empty bmp_bytes"):
        GraphicBuildEntry(name="wiki-mark", bmp_bytes=b"")
