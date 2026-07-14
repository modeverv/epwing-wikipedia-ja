from __future__ import annotations

import pytest

from wikiepwing.render.render_node import TextRenderNode
from wikiepwing.render.rendered_entry import RenderedEntry, RenderedEntryError


def _make_entry(**overrides: object) -> RenderedEntry:
    defaults: dict[str, object] = {
        "entry_id": "p1",
        "page_id": 1,
        "title": "Emacs",
        "headwords": ("Emacs", "GNU Emacs"),
        "body": (TextRenderNode(text="An extensible editor."),),
        "internal_targets": ("p2",),
        "graphics": (),
        "estimated_size": 128,
        "diagnostics": (),
    }
    defaults.update(overrides)
    return RenderedEntry(**defaults)  # type: ignore[arg-type]


def test_rendered_entry_round_trips_fields() -> None:
    entry = _make_entry()

    assert entry.entry_id == "p1"
    assert entry.page_id == 1
    assert entry.headwords == ("Emacs", "GNU Emacs")
    assert entry.body == (TextRenderNode(text="An extensible editor."),)


def test_rendered_entry_rejects_empty_entry_id() -> None:
    with pytest.raises(RenderedEntryError, match="entry_id"):
        _make_entry(entry_id="")


def test_rendered_entry_rejects_non_positive_page_id() -> None:
    with pytest.raises(RenderedEntryError, match="page_id"):
        _make_entry(page_id=0)


def test_rendered_entry_rejects_empty_title() -> None:
    with pytest.raises(RenderedEntryError, match="title"):
        _make_entry(title="")


def test_rendered_entry_rejects_negative_estimated_size() -> None:
    with pytest.raises(RenderedEntryError, match="estimated_size"):
        _make_entry(estimated_size=-1)


def test_rendered_entry_allows_zero_estimated_size() -> None:
    entry = _make_entry(estimated_size=0)

    assert entry.estimated_size == 0
