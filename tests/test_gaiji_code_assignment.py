from __future__ import annotations

import pytest

from wikiepwing.gaiji.code_assignment import (
    MAX_GAIJI_PER_WIDTH,
    GaijiCodeAssignmentError,
    assign_gaiji_codes,
)


def test_assigns_sequential_codes_per_width_class() -> None:
    result = assign_gaiji_codes([("A", "narrow"), ("B", "narrow")])

    assert result == {"A": "narrow-0001", "B": "narrow-0002"}


def test_narrow_and_wide_have_independent_code_spaces() -> None:
    result = assign_gaiji_codes([("A", "narrow"), ("B", "wide")])

    assert result == {"A": "narrow-0001", "B": "wide-0001"}


def test_assignment_follows_unicode_sort_order_not_input_order() -> None:
    result = assign_gaiji_codes([("Z", "narrow"), ("A", "narrow"), ("M", "narrow")])

    assert result == {"A": "narrow-0001", "M": "narrow-0002", "Z": "narrow-0003"}


def test_assignment_is_deterministic_regardless_of_input_order() -> None:
    forward = assign_gaiji_codes([("A", "narrow"), ("B", "narrow"), ("C", "narrow")])
    shuffled = assign_gaiji_codes([("C", "narrow"), ("A", "narrow"), ("B", "narrow")])

    assert forward == shuffled


def test_empty_input_returns_empty_mapping() -> None:
    assert assign_gaiji_codes([]) == {}


def test_invalid_width_class_raises() -> None:
    with pytest.raises(GaijiCodeAssignmentError, match="width_class"):
        assign_gaiji_codes([("A", "medium")])


def test_duplicate_sequence_raises() -> None:
    with pytest.raises(GaijiCodeAssignmentError, match="duplicate"):
        assign_gaiji_codes([("A", "narrow"), ("A", "wide")])


def test_codes_are_zero_padded_to_four_digits() -> None:
    entries = [(chr(ord("a") + i), "narrow") for i in range(12)]

    result = assign_gaiji_codes(entries)

    assert result["a"] == "narrow-0001"
    assert result["l"] == "narrow-0012"


def test_backend_capacity_is_enforced_per_width() -> None:
    entries = [(f"character-{index}", "wide") for index in range(MAX_GAIJI_PER_WIDTH + 1)]

    with pytest.raises(GaijiCodeAssignmentError, match="exceeds backend limit 8192"):
        assign_gaiji_codes(entries)


def test_custom_capacity_must_be_non_negative() -> None:
    with pytest.raises(GaijiCodeAssignmentError, match="non-negative"):
        assign_gaiji_codes([], max_per_width=-1)
