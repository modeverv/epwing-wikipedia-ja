from __future__ import annotations

from pathlib import Path

import pytest

from wikiepwing.reference.scanner import ReferencePathError, validate_reference_path


@pytest.fixture(autouse=True)
def _restore_fixture_permissions(tmp_path: Path) -> None:
    yield
    paths = sorted(tmp_path.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    for path in paths:
        if path.is_symlink():
            continue
        path.chmod(0o755 if path.is_dir() else 0o644)
    tmp_path.chmod(0o755)


def _make_read_only(path: Path) -> None:
    path.chmod(0o555 if path.is_dir() else 0o444)


def test_validate_reference_path_discovers_sorted_bounded_catalogs(tmp_path: Path) -> None:
    reference = tmp_path / "reference"
    first_book = reference / "A_BOOK"
    second_book = reference / "B_BOOK"
    first_book.mkdir(parents=True)
    second_book.mkdir()
    first_catalog = first_book / "catalogs"
    second_catalog = second_book / "CATALOGS"
    first_catalog.write_bytes(b"\0" * 2048)
    second_catalog.write_bytes(b"\1" * 4096)
    for path in (first_catalog, second_catalog, first_book, second_book, reference):
        _make_read_only(path)

    result = validate_reference_path(reference)

    assert result.root == reference.resolve()
    assert result.catalogs == (first_catalog.resolve(), second_catalog.resolve())
    assert result.visited_entries == 4


def test_validate_reference_path_rejects_writable_root_without_writing(tmp_path: Path) -> None:
    reference = tmp_path / "reference"
    reference.mkdir()
    before = tuple(reference.iterdir())

    with pytest.raises(ReferencePathError, match="must be read-only"):
        validate_reference_path(reference)

    assert tuple(reference.iterdir()) == before


def test_validate_reference_path_does_not_follow_catalog_or_directory_symlinks(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "CATALOGS").write_bytes(b"\0" * 2048)
    reference = tmp_path / "reference"
    reference.mkdir()
    (reference / "CATALOGS").symlink_to(outside / "CATALOGS")
    (reference / "book-link").symlink_to(outside, target_is_directory=True)
    _make_read_only(reference)

    with pytest.raises(ReferencePathError, match="no regular CATALOGS file"):
        validate_reference_path(reference)


@pytest.mark.parametrize("size", [0, 2049, 1024 * 1024 + 2048])
def test_validate_reference_path_rejects_invalid_catalog_size(tmp_path: Path, size: int) -> None:
    reference = tmp_path / "reference"
    reference.mkdir()
    catalog = reference / "CATALOGS"
    catalog.write_bytes(b"\0" * size)
    _make_read_only(catalog)
    _make_read_only(reference)

    with pytest.raises(ReferencePathError, match="invalid CATALOGS size"):
        validate_reference_path(reference)


def test_validate_reference_path_rejects_relative_file_and_symlink_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    regular_file = tmp_path / "reference-file"
    regular_file.write_bytes(b"x")
    link = tmp_path / "reference-link"
    link.symlink_to(regular_file)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ReferencePathError, match="must be absolute"):
        validate_reference_path(Path("reference-file"))
    with pytest.raises(ReferencePathError, match="must not be a symlink"):
        validate_reference_path(link)
