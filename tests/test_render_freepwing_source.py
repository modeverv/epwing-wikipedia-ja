from __future__ import annotations

import json
from pathlib import Path

import pytest

from wikiepwing.render.freepwing_source import write_entries_jsonl_stream
from wikiepwing.render.render_node import GraphicRenderNode, LinkRenderNode, TextRenderNode
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

    write_entries_jsonl_stream(lambda: (_make_entry(),), destination)

    lines = destination.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record == {
        "tag": "p1",
        "title": "Emacs",
        "heading": "Emacs",
        "aliases": ["GNU Emacs"],
        "keywords": [],
        "body": "line one\nline two",
        "targets": ["p2"],
    }


def test_write_entries_jsonl_keeps_search_title_separate_from_display_heading(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "entries.jsonl"
    entry = _make_entry(heading="日本 (アルバム)〔にほん〕")

    write_entries_jsonl_stream(lambda: (entry,), destination)

    record = json.loads(destination.read_text(encoding="utf-8"))
    assert record["title"] == "Emacs"
    assert record["heading"] == "日本 (アルバム)〔にほん〕"


def test_write_entries_jsonl_handles_no_aliases_and_no_targets(tmp_path: Path) -> None:
    destination = tmp_path / "entries.jsonl"
    entry = _make_entry(headwords=("Emacs",), internal_targets=())

    write_entries_jsonl_stream(lambda: (entry,), destination)

    record = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert record["aliases"] == []
    assert record["targets"] == []


def test_write_entries_jsonl_writes_multiple_entries_in_order(tmp_path: Path) -> None:
    destination = tmp_path / "entries.jsonl"
    entries = (
        _make_entry(entry_id="p1", page_id=1, title="Emacs"),
        _make_entry(entry_id="p2", page_id=2, title="Linux", headwords=("Linux",)),
    )

    write_entries_jsonl_stream(lambda: entries, destination)

    lines = destination.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["tag"] == "p1"
    assert json.loads(lines[1])["tag"] == "p2"


def test_write_entries_jsonl_creates_parent_directories(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "dir" / "entries.jsonl"

    write_entries_jsonl_stream(lambda: (_make_entry(),), destination)

    assert destination.is_file()


def test_write_entries_jsonl_preserves_multiline_body(tmp_path: Path) -> None:
    destination = tmp_path / "entries.jsonl"
    entry = _make_entry(body=(TextRenderNode(text="a\nb\nc"),))

    write_entries_jsonl_stream(lambda: (entry,), destination)

    record = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert record["body"] == "a\nb\nc"


def test_write_entries_jsonl_serializes_inline_link_at_body_position(tmp_path: Path) -> None:
    destination = tmp_path / "entries.jsonl"
    entry = _make_entry(
        body=(
            TextRenderNode(text="See "),
            LinkRenderNode(label="GNU Project", target="p2"),
            TextRenderNode(text=" now."),
        )
    )

    write_entries_jsonl_stream(lambda: (entry,), destination)

    record = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert record["body"] == "See \x1eR:p2\x1fGNU Project\x1eE\x1f now."


def test_write_entries_jsonl_serializes_graphic_at_body_position(tmp_path: Path) -> None:
    destination = tmp_path / "entries.jsonl"
    entry = _make_entry(
        body=(
            TextRenderNode(text="before\n"),
            GraphicRenderNode(name="abc123"),
            TextRenderNode(text="\nafter"),
        ),
        graphics=("abc123",),
    )

    write_entries_jsonl_stream(lambda: (entry,), destination)

    record = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert record["body"] == "before\n\x1eG:abc123\x1f\nafter"


def test_write_entries_jsonl_does_not_touch_destination_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "entries.jsonl"
    destination.write_text("original\n", encoding="utf-8")

    def _broken_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated failure")

    monkeypatch.setattr("os.replace", _broken_replace)

    with pytest.raises(OSError, match="simulated failure"):
        write_entries_jsonl_stream(lambda: (_make_entry(),), destination)

    assert destination.read_text(encoding="utf-8") == "original\n"


def test_write_entries_jsonl_replaces_gaiji_candidate_body_characters_with_tokens(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "entries.jsonl"
    # U+4E02 ("丂") is JIS X 0212-only (SS3): not backend-representable.
    entry = _make_entry(body=(TextRenderNode(text="before 丂 after"),))

    plan = write_entries_jsonl_stream(lambda: (entry,), destination)

    assert not plan.is_empty()
    code = plan.assigned_codes["丂"]
    record = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert record["body"] == f"before @@GAIJI:{code}@@ after"


def test_write_entries_jsonl_never_embeds_gaiji_tokens_in_title_or_aliases(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "entries.jsonl"
    entry = _make_entry(title="丂 Title", headwords=("丂 Title", "丂 Alias"))

    write_entries_jsonl_stream(lambda: (entry,), destination)

    record = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert record["title"] == "[U+4E02] Title"
    assert record["aliases"] == ["[U+4E02] Alias"]
    assert "@@GAIJI:" not in record["title"]
    assert "@@GAIJI:" not in record["aliases"][0]


def test_write_entries_jsonl_leaves_fully_representable_text_unchanged(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "entries.jsonl"

    plan = write_entries_jsonl_stream(lambda: (_make_entry(),), destination)

    assert plan.is_empty()
    record = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert record["title"] == "Emacs"
    assert record["body"] == "line one\nline two"
