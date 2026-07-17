from __future__ import annotations

import pytest

from wikiepwing.gaiji.unrepresentable import (
    UnrepresentableTracker,
    unrepresentable_fallback,
)


def test_fallback_uses_four_digit_uppercase_hex() -> None:
    assert unrepresentable_fallback("\x01") == "[U+0001]"


def test_fallback_uses_uppercase_hex_for_bmp_character() -> None:
    assert unrepresentable_fallback("￿") == "[U+FFFF]"


def test_fallback_extends_digits_for_supplementary_plane() -> None:
    assert unrepresentable_fallback("😀") == "[U+1F600]"


def test_tracker_counts_occurrences_of_one_character() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("😀")
    tracker.record("😀")

    stats = tracker.most_frequent()

    assert len(stats) == 1
    assert stats[0].character == "😀"
    assert stats[0].count == 2


def test_tracker_records_repeated_occurrences_in_one_call() -> None:
    tracker = UnrepresentableTracker(max_examples_per_character=2)

    tracker.record_many("😀", 5, page_id=7, title="Repeated")

    stat = tracker.most_frequent()[0]
    assert stat.count == 5
    assert len(stat.examples) == 2
    assert all(example.page_id == 7 for example in stat.examples)


def test_tracker_rejects_negative_repeated_count() -> None:
    tracker = UnrepresentableTracker()

    with pytest.raises(ValueError, match="count must not be negative"):
        tracker.record_many("😀", -1)


def test_tracker_orders_by_count_descending() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("A")
    tracker.record("B")
    tracker.record("B")
    tracker.record("B")

    stats = tracker.most_frequent()

    assert [stat.character for stat in stats] == ["B", "A"]


def test_tracker_breaks_ties_by_codepoint_ascending() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("Z")
    tracker.record("A")

    stats = tracker.most_frequent()

    assert [stat.character for stat in stats] == ["A", "Z"]


def test_tracker_most_frequent_respects_limit() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("A")
    tracker.record("B")
    tracker.record("C")

    stats = tracker.most_frequent(limit=2)

    assert len(stats) == 2


def test_tracker_caps_examples_but_not_the_count() -> None:
    tracker = UnrepresentableTracker(max_examples_per_character=2)
    for page_id in range(1, 6):
        tracker.record("A", page_id=page_id, title=f"Article {page_id}")

    stats = tracker.most_frequent()

    assert stats[0].count == 5
    assert len(stats[0].examples) == 2
    assert stats[0].examples[0].page_id == 1
    assert stats[0].examples[1].page_id == 2


def test_tracker_examples_carry_page_id_and_title() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("A", page_id=42, title="Some Article")

    stats = tracker.most_frequent()

    assert stats[0].examples[0].page_id == 42
    assert stats[0].examples[0].title == "Some Article"


def test_tracker_total_occurrences_sums_across_characters() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("A")
    tracker.record("A")
    tracker.record("B")

    assert tracker.total_occurrences() == 3


def test_tracker_characters_returns_distinct_tracked_characters() -> None:
    tracker = UnrepresentableTracker()
    tracker.record("A")
    tracker.record("A")
    tracker.record("B")

    assert set(tracker.characters()) == {"A", "B"}


def test_tracker_rejects_negative_max_examples() -> None:
    with pytest.raises(ValueError, match="max_examples_per_character"):
        UnrepresentableTracker(max_examples_per_character=-1)


def test_tracker_with_zero_max_examples_still_counts() -> None:
    tracker = UnrepresentableTracker(max_examples_per_character=0)
    tracker.record("A", page_id=1)

    stats = tracker.most_frequent()

    assert stats[0].count == 1
    assert stats[0].examples == ()
