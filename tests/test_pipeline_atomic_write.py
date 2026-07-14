from __future__ import annotations

from pathlib import Path

import pytest

from wikiepwing.pipeline.atomic_write import atomic_write_bytes, atomic_write_text


def test_atomic_write_text_writes_full_content(tmp_path: Path) -> None:
    destination = tmp_path / "out.txt"

    atomic_write_text(destination, "hello world")

    assert destination.read_text(encoding="utf-8") == "hello world"


def test_atomic_write_bytes_writes_full_content(tmp_path: Path) -> None:
    destination = tmp_path / "out.bin"

    atomic_write_bytes(destination, b"\x00\x01\x02")

    assert destination.read_bytes() == b"\x00\x01\x02"


def test_atomic_write_creates_parent_directories(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "dir" / "out.txt"

    atomic_write_text(destination, "x")

    assert destination.is_file()


def test_atomic_write_overwrites_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "out.txt"
    destination.write_text("old", encoding="utf-8")

    atomic_write_text(destination, "new")

    assert destination.read_text(encoding="utf-8") == "new"


def test_atomic_write_leaves_no_temp_files_behind(tmp_path: Path) -> None:
    destination = tmp_path / "out.txt"

    atomic_write_text(destination, "hello")

    assert list(tmp_path.iterdir()) == [destination]


def test_failed_write_does_not_touch_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "out.txt"
    destination.write_text("original", encoding="utf-8")

    def _broken_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated failure")

    monkeypatch.setattr("os.replace", _broken_replace)

    with pytest.raises(OSError, match="simulated failure"):
        atomic_write_text(destination, "new content")

    assert destination.read_text(encoding="utf-8") == "original"
