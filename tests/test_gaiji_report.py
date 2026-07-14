from __future__ import annotations

import json
from pathlib import Path

from wikiepwing.gaiji.report import build_unicode_report, write_unicode_report
from wikiepwing.gaiji.unrepresentable import UnrepresentableTracker


def test_build_unicode_report_summarizes_tracker() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("😀", page_id=1, title="Emoji Article")
    tracker.record("😀", page_id=2, title="Other Article")
    tracker.record("🗼", page_id=1, title="Emoji Article")

    report = build_unicode_report(tracker)

    assert report.schema_version == 1
    assert report.total_occurrences == 3
    assert report.distinct_characters == 2


def test_build_unicode_report_orders_characters_by_frequency() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("A")
    tracker.record("B")
    tracker.record("B")

    report = build_unicode_report(tracker)

    assert [entry["character"] for entry in report.characters] == ["B", "A"]


def test_build_unicode_report_includes_code_point_and_examples() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("😀", page_id=42, title="Some Article")

    report = build_unicode_report(tracker)

    entry = report.characters[0]
    assert entry["code_point"] == "U+1F600"
    assert entry["count"] == 1
    assert entry["examples"] == [{"page_id": 42, "title": "Some Article"}]


def test_build_unicode_report_with_empty_tracker() -> None:
    report = build_unicode_report(UnrepresentableTracker())

    assert report.total_occurrences == 0
    assert report.distinct_characters == 0
    assert report.characters == ()


def test_write_unicode_report_writes_valid_json(tmp_path: Path) -> None:
    tracker = UnrepresentableTracker()
    tracker.record("😀", page_id=1, title="Emoji Article")
    report = build_unicode_report(tracker)
    destination = tmp_path / "unicode-report.json"

    result_path = write_unicode_report(report, destination)

    assert result_path == destination
    written = json.loads(destination.read_text(encoding="utf-8"))
    assert written == report.payload()


def test_write_unicode_report_creates_parent_directories(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "dir" / "unicode-report.json"

    write_unicode_report(build_unicode_report(UnrepresentableTracker()), destination)

    assert destination.is_file()
