"""Unicode report (TASK-M009, ARCHITECTURE.md 18.5).

18.5 requires a build to report unrepresentable (category-D) character
occurrences by count, frequency rank, and example articles.
TASK-M008's `UnrepresentableTracker` already aggregates that; this module
assembles it into one JSON-serializable report and writes it atomically
(reusing TASK-I004's `atomic_write_text` rather than duplicating that
logic). This intentionally does not replicate `reference/report.py`'s
heavier JSON+HTML+Markdown deliverable -- 18.5 asks only for the three
data points this report carries.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from wikiepwing.gaiji.unrepresentable import UnrepresentableTracker
from wikiepwing.pipeline.atomic_write import atomic_write_text

REPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class UnicodeReport:
    """A build's unrepresentable-character occurrence report."""

    schema_version: int
    total_occurrences: int
    distinct_characters: int
    characters: tuple[dict[str, object], ...]

    def payload(self) -> dict[str, object]:
        """Return this report as a JSON-serializable mapping."""
        return {
            "schema_version": self.schema_version,
            "total_occurrences": self.total_occurrences,
            "distinct_characters": self.distinct_characters,
            "characters": list(self.characters),
        }


def build_unicode_report(tracker: UnrepresentableTracker) -> UnicodeReport:
    """Build a UnicodeReport from `tracker`'s accumulated statistics."""
    stats = tracker.most_frequent()
    characters = tuple(
        {
            "character": stat.character,
            "code_point": f"U+{ord(stat.character):04X}",
            "count": stat.count,
            "examples": [
                {"page_id": example.page_id, "title": example.title} for example in stat.examples
            ],
        }
        for stat in stats
    )
    return UnicodeReport(
        schema_version=REPORT_SCHEMA_VERSION,
        total_occurrences=tracker.total_occurrences(),
        distinct_characters=len(stats),
        characters=characters,
    )


def write_unicode_report(report: UnicodeReport, destination: Path) -> Path:
    """Write `report` as JSON to `destination`, atomically."""
    text = json.dumps(report.payload(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    atomic_write_text(destination, text)
    return destination
