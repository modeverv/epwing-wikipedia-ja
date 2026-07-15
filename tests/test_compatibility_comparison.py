from __future__ import annotations

import pytest

from wikiepwing.compatibility.comparison import QueryHitSet, compare_query_results


def _hit_set(key: str, expected_presence: bool, headings: tuple[str, ...]) -> QueryHitSet:
    return QueryHitSet(query_key=key, expected_presence=expected_presence, headings=headings)


def test_expected_presence_true_with_a_hit_covers() -> None:
    reference = [_hit_set("q1", True, ("Emacs",))]
    candidate = [_hit_set("q1", True, ("Emacs",))]

    summary = compare_query_results(reference, candidate)

    assert summary.per_query[0].presence_matches_expectation is True
    assert summary.target_coverage == 1.0


def test_expected_presence_true_with_no_hit_does_not_cover() -> None:
    reference = [_hit_set("q1", True, ("Emacs",))]
    candidate = [_hit_set("q1", True, ())]

    summary = compare_query_results(reference, candidate)

    assert summary.per_query[0].presence_matches_expectation is False
    assert summary.target_coverage == 0.0


def test_expected_presence_false_with_no_hit_covers() -> None:
    reference = [_hit_set("missing", False, ())]
    candidate = [_hit_set("missing", False, ())]

    summary = compare_query_results(reference, candidate)

    assert summary.per_query[0].presence_matches_expectation is True
    assert summary.false_positive_count == 0


def test_expected_presence_false_with_a_hit_is_a_false_positive() -> None:
    reference = [_hit_set("missing", False, ())]
    candidate = [_hit_set("missing", False, ("Unexpected Hit",))]

    summary = compare_query_results(reference, candidate)

    assert summary.per_query[0].presence_matches_expectation is False
    assert summary.false_positive_count == 1


def test_target_coverage_is_the_fraction_of_matching_queries() -> None:
    reference = [
        _hit_set("q1", True, ("A",)),
        _hit_set("q2", True, ("B",)),
        _hit_set("q3", False, ()),
        _hit_set("q4", True, ()),
    ]
    candidate = [
        _hit_set("q1", True, ("A",)),
        _hit_set("q2", True, ()),
        _hit_set("q3", False, ()),
        _hit_set("q4", True, ()),
    ]

    summary = compare_query_results(reference, candidate)

    assert summary.total == 4
    assert summary.target_coverage == 0.5


def test_overlap_at_n_computed_by_heading_intersection() -> None:
    reference = [_hit_set("q1", True, ("A", "B", "C"))]
    candidate = [_hit_set("q1", True, ("B", "C", "D"))]

    summary = compare_query_results(reference, candidate)

    assert summary.per_query[0].overlap_at_n == pytest.approx(2 / 3)


def test_overlap_at_n_is_none_when_reference_headings_are_empty() -> None:
    reference = [_hit_set("q1", False, ())]
    candidate = [_hit_set("q1", False, ())]

    summary = compare_query_results(reference, candidate)

    assert summary.per_query[0].overlap_at_n is None
    assert summary.overlap_at_n_mean is None


def test_overlap_at_n_mean_averages_over_queries_with_a_defined_overlap() -> None:
    reference = [
        _hit_set("q1", True, ("A", "B")),
        _hit_set("q2", True, ("A", "B")),
        _hit_set("q3", False, ()),
    ]
    candidate = [
        _hit_set("q1", True, ("A", "B")),
        _hit_set("q2", True, ("A",)),
        _hit_set("q3", False, ()),
    ]

    summary = compare_query_results(reference, candidate)

    assert summary.overlap_at_n_mean == pytest.approx((1.0 + 0.5) / 2)


def test_missing_candidate_query_key_raises() -> None:
    reference = [_hit_set("q1", True, ("A",))]
    candidate: list[QueryHitSet] = []

    with pytest.raises(ValueError, match="q1"):
        compare_query_results(reference, candidate)


def test_empty_reference_yields_zero_total_and_zero_coverage() -> None:
    summary = compare_query_results([], [])

    assert summary.total == 0
    assert summary.target_coverage == 0.0
    assert summary.false_positive_count == 0
    assert summary.overlap_at_n_mean is None
    assert summary.per_query == ()
