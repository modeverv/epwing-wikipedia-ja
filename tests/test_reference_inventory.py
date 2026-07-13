from __future__ import annotations

import json
from pathlib import Path

import pytest

from wikiepwing.reference.inventory import (
    ReferenceInventoryError,
    build_reference_inventory,
    write_reference_inventory,
)


@pytest.fixture(autouse=True)
def _restore_fixture_permissions(tmp_path: Path) -> None:
    yield
    paths = sorted(tmp_path.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    for path in paths:
        if path.is_symlink():
            continue
        path.chmod(0o755 if path.is_dir() else 0o644)
    tmp_path.chmod(0o755)


def _make_read_only_tree(root: Path) -> None:
    paths = sorted(root.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    for path in paths:
        if path.is_symlink():
            continue
        path.chmod(0o555 if path.is_dir() else 0o444)
    root.chmod(0o555)


def _make_reference(tmp_path: Path) -> Path:
    root = tmp_path / "reference"
    data = root / "WIKIP" / "DATA"
    gaiji = root / "WIKIP" / "GAIJI"
    data.mkdir(parents=True)
    gaiji.mkdir()
    (root / "CATALOGS").write_bytes(b"\0" * 2048)
    (data / "HONMON.EBZ").write_bytes(b"body")
    (gaiji / "GAI16H.EBZ").write_bytes(b"font")
    (root / "wikip.css").write_text("body {}", encoding="ascii")
    outside = tmp_path / "outside"
    outside.write_text("do not follow", encoding="ascii")
    (root / "outside-link").symlink_to(outside)
    _make_read_only_tree(root)
    return root


def test_inventory_is_sorted_summarized_and_finds_subbook_candidates(tmp_path: Path) -> None:
    root = _make_reference(tmp_path)

    inventory = build_reference_inventory(root)
    payload = inventory.payload()

    paths = [entry["path"] for entry in payload["entries"]]
    assert paths == sorted(paths, key=lambda path: (path.casefold(), path))
    assert payload["schema_version"] == 1
    assert payload["root"] == str(root.resolve())
    assert payload["summary"] == {
        "directory_count": 3,
        "file_count": 4,
        "other_count": 0,
        "symlink_count": 1,
        "total_file_bytes": 2063,
    }
    assert payload["subbook_candidates"] == [
        {
            "catalog_path": "CATALOGS",
            "directory": "WIKIP",
            "gaiji_paths": ["WIKIP/GAIJI/GAI16H.EBZ"],
            "honmon_paths": ["WIKIP/DATA/HONMON.EBZ"],
            "name": "WIKIP",
        }
    ]
    link = next(entry for entry in payload["entries"] if entry["path"] == "outside-link")
    assert link == {"kind": "symlink", "path": "outside-link", "size_bytes": None}


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_entries": 2}, "entry limit"),
        ({"max_depth": 1}, "depth limit"),
        ({"max_path_bytes": 5}, "path byte limit"),
    ],
)
def test_inventory_rejects_safety_limit_overruns(
    tmp_path: Path, kwargs: dict[str, int], message: str
) -> None:
    root = _make_reference(tmp_path)

    with pytest.raises(ReferenceInventoryError, match=message):
        build_reference_inventory(root, **kwargs)


def test_inventory_json_is_stable_and_cannot_be_written_inside_reference(
    tmp_path: Path,
) -> None:
    root = _make_reference(tmp_path)
    inventory = build_reference_inventory(root)
    output = tmp_path / "reports" / "inventory.json"

    write_reference_inventory(inventory, output)
    first = output.read_bytes()
    write_reference_inventory(inventory, output)

    assert output.read_bytes() == first
    assert json.loads(first)["summary"]["file_count"] == 4
    with pytest.raises(ReferenceInventoryError, match="outside reference root"):
        write_reference_inventory(inventory, root / "inventory.json")
