from __future__ import annotations

import json
from pathlib import Path

from wikiepwing.render.freepwing_source import write_entries_jsonl
from wikiepwing.render.render_node import TextRenderNode
from wikiepwing.render.rendered_entry import RenderedEntry


def _make_entry(**overrides: object) -> RenderedEntry:
    defaults: dict[str, object] = {
        "entry_id": "p1",
        "page_id": 1,
        "title": "Emacs",
        "headwords": ("Emacs", "GNU Emacs"),
        "body": (TextRenderNode(text="line one\nline two"),),
        "internal_targets": ("p2",),
        "graphics": (),
        "estimated_size": 10,
        "diagnostics": (),
    }
    defaults.update(overrides)
    return RenderedEntry(**defaults)  # type: ignore[arg-type]


def test_write_entries_jsonl_writes_one_json_object_per_line(tmp_path: Path) -> None:
    destination = tmp_path / "entries.jsonl"

    write_entries_jsonl((_make_entry(),), destination)

    lines = destination.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record == {
        "tag": "p1",
        "title": "Emacs",
        "aliases": ["GNU Emacs"],
        "body": "line one\nline two",
        "targets": ["p2"],
    }


def test_write_entries_jsonl_handles_no_aliases_and_no_targets(tmp_path: Path) -> None:
    destination = tmp_path / "entries.jsonl"
    entry = _make_entry(headwords=("Emacs",), internal_targets=())

    write_entries_jsonl((entry,), destination)

    record = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert record["aliases"] == []
    assert record["targets"] == []


def test_write_entries_jsonl_writes_multiple_entries_in_order(tmp_path: Path) -> None:
    destination = tmp_path / "entries.jsonl"
    entries = (
        _make_entry(entry_id="p1", page_id=1, title="Emacs"),
        _make_entry(entry_id="p2", page_id=2, title="Linux", headwords=("Linux",)),
    )

    write_entries_jsonl(entries, destination)

    lines = destination.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["tag"] == "p1"
    assert json.loads(lines[1])["tag"] == "p2"


def test_write_entries_jsonl_creates_parent_directories(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "dir" / "entries.jsonl"

    write_entries_jsonl((_make_entry(),), destination)

    assert destination.is_file()


def test_write_entries_jsonl_preserves_multiline_body(tmp_path: Path) -> None:
    destination = tmp_path / "entries.jsonl"
    entry = _make_entry(body=(TextRenderNode(text="a\nb\nc"),))

    write_entries_jsonl((entry,), destination)

    record = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert record["body"] == "a\nb\nc"
