from __future__ import annotations

import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.archive import build_deterministic_archive

_TIMESTAMP = datetime(2000, 1, 1, tzinfo=UTC)


def _make_source_dir(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    (source / "WIKIEP" / "DATA").mkdir(parents=True)
    (source / "WIKIEP" / "DATA" / "HONMON").write_bytes(b"honmon-bytes")
    (source / "CATALOGS").write_bytes(b"catalogs-bytes")
    return source


def test_archive_contains_every_file_with_root_prefix(tmp_path: Path) -> None:
    source = _make_source_dir(tmp_path)
    archive_path = tmp_path / "book.epwing.zip"

    build_deterministic_archive(
        source, archive_path, root_directory_name="book", archive_timestamp=_TIMESTAMP
    )

    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())

    assert names == {"book/CATALOGS", "book/WIKIEP/DATA/HONMON"}


def test_archive_entries_use_the_fixed_timestamp(tmp_path: Path) -> None:
    source = _make_source_dir(tmp_path)
    archive_path = tmp_path / "book.epwing.zip"

    build_deterministic_archive(
        source, archive_path, root_directory_name="book", archive_timestamp=_TIMESTAMP
    )

    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            assert info.date_time == (2000, 1, 1, 0, 0, 0)


def test_archive_is_byte_identical_across_two_builds(tmp_path: Path) -> None:
    source = _make_source_dir(tmp_path)
    first_path = tmp_path / "first.zip"
    second_path = tmp_path / "second.zip"

    build_deterministic_archive(
        source, first_path, root_directory_name="book", archive_timestamp=_TIMESTAMP
    )
    build_deterministic_archive(
        source, second_path, root_directory_name="book", archive_timestamp=_TIMESTAMP
    )

    assert first_path.read_bytes() == second_path.read_bytes()


def test_archive_changes_when_file_content_changes(tmp_path: Path) -> None:
    source = _make_source_dir(tmp_path)
    first_path = tmp_path / "first.zip"
    build_deterministic_archive(
        source, first_path, root_directory_name="book", archive_timestamp=_TIMESTAMP
    )

    (source / "CATALOGS").write_bytes(b"different-bytes")
    second_path = tmp_path / "second.zip"
    build_deterministic_archive(
        source, second_path, root_directory_name="book", archive_timestamp=_TIMESTAMP
    )

    assert first_path.read_bytes() != second_path.read_bytes()


def test_archive_changes_when_root_directory_name_changes(tmp_path: Path) -> None:
    source = _make_source_dir(tmp_path)
    first_path = tmp_path / "first.zip"
    second_path = tmp_path / "second.zip"

    build_deterministic_archive(
        source, first_path, root_directory_name="book-a", archive_timestamp=_TIMESTAMP
    )
    build_deterministic_archive(
        source, second_path, root_directory_name="book-b", archive_timestamp=_TIMESTAMP
    )

    assert first_path.read_bytes() != second_path.read_bytes()


def test_rejects_naive_archive_timestamp(tmp_path: Path) -> None:
    source = _make_source_dir(tmp_path)
    archive_path = tmp_path / "book.epwing.zip"

    with pytest.raises(ValueError, match="timezone-aware"):
        build_deterministic_archive(
            source, archive_path, root_directory_name="book", archive_timestamp=datetime(2000, 1, 1)
        )


def test_rejects_empty_root_directory_name(tmp_path: Path) -> None:
    source = _make_source_dir(tmp_path)
    archive_path = tmp_path / "book.epwing.zip"

    with pytest.raises(ValueError, match="root_directory_name"):
        build_deterministic_archive(
            source, archive_path, root_directory_name="", archive_timestamp=_TIMESTAMP
        )


def test_creates_missing_destination_directory(tmp_path: Path) -> None:
    source = _make_source_dir(tmp_path)
    archive_path = tmp_path / "nested" / "book.epwing.zip"

    build_deterministic_archive(
        source, archive_path, root_directory_name="book", archive_timestamp=_TIMESTAMP
    )

    assert archive_path.is_file()


def test_does_not_leave_temporary_files_behind(tmp_path: Path) -> None:
    source = _make_source_dir(tmp_path)
    archive_path = tmp_path / "book.epwing.zip"

    build_deterministic_archive(
        source, archive_path, root_directory_name="book", archive_timestamp=_TIMESTAMP
    )

    remaining = list(tmp_path.glob("*.tmp"))
    assert remaining == []
