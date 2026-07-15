"""Reference comparison engine (TASK-Q007, COMPATIBILITY.md 5/13).

Computes 5.2's three fixed-query metrics between the reference
dictionary's recorded search results (TASK-C006's `reference/searches.py`
persistence, summarized by TASK-C007's reference report) and a
candidate build's results for the *same* fixed query set:

- Result presence / Target coverage: whether a query's actual hit
  presence matches its `expected_presence` (TASK-Q001-adjacent fixture
  field, `reference.queries.FixedQuery`). Per 5.3's "missing query
  returns false exact hit: 0", a query expected to be *absent*
  (`expected_presence=False`) only "covers" when the candidate finds
  *zero* hits -- any hit at all is a false positive.
- Overlap@N: `|candidate_top_n ∩ reference_top_n| / |reference_top_n|`,
  comparing by heading text rather than entry locator, since a locator
  is backend/build-specific and never comparable across two different
  builds (even a byte-identical article moves to a different offset).

Actually running the candidate's searches (an EB search adapter driven
against a real built dictionary, requiring the full toolchain) is out of
scope here -- this module only compares two already-computed result
sets, mirroring how TASK-C006/reference/searches.py's search execution
and TASK-C007/reference/report.py's report generation stay separate.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueryHitSet:
    """One fixed query's top-N heading hits, from either side of the comparison."""

    query_key: str
    expected_presence: bool
    headings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QueryComparison:
    """One query's comparison outcome."""

    query_key: str
    expected_presence: bool
    candidate_present: bool
    presence_matches_expectation: bool
    overlap_at_n: float | None


@dataclass(frozen=True, slots=True)
class ComparisonSummary:
    """The aggregate comparison result across every fixed query (COMPATIBILITY.md 13)."""

    total: int
    target_coverage: float
    false_positive_count: int
    overlap_at_n_mean: float | None
    per_query: tuple[QueryComparison, ...]


def compare_query_results(
    reference: Sequence[QueryHitSet], candidate: Sequence[QueryHitSet]
) -> ComparisonSummary:
    """Compare `candidate`'s results against `reference`'s for the same fixed query set.

    Every `reference` query must have a matching `candidate` entry
    (same `query_key`); a missing one raises `ValueError` rather than
    silently producing a partial comparison.
    """
    candidate_by_key = {hit_set.query_key: hit_set for hit_set in candidate}

    per_query: list[QueryComparison] = []
    covered = 0
    false_positives = 0
    overlaps: list[float] = []

    for reference_hit_set in reference:
        candidate_hit_set = candidate_by_key.get(reference_hit_set.query_key)
        if candidate_hit_set is None:
            raise ValueError(
                f"candidate results are missing query_key: {reference_hit_set.query_key!r}"
            )

        candidate_present = len(candidate_hit_set.headings) > 0
        expected_presence = reference_hit_set.expected_presence
        matches = candidate_present == expected_presence
        if matches:
            covered += 1
        if not expected_presence and candidate_present:
            false_positives += 1

        overlap_at_n = _overlap_at_n(reference_hit_set.headings, candidate_hit_set.headings)
        if overlap_at_n is not None:
            overlaps.append(overlap_at_n)

        per_query.append(
            QueryComparison(
                query_key=reference_hit_set.query_key,
                expected_presence=expected_presence,
                candidate_present=candidate_present,
                presence_matches_expectation=matches,
                overlap_at_n=overlap_at_n,
            )
        )

    total = len(reference)
    return ComparisonSummary(
        total=total,
        target_coverage=covered / total if total else 0.0,
        false_positive_count=false_positives,
        overlap_at_n_mean=sum(overlaps) / len(overlaps) if overlaps else None,
        per_query=tuple(per_query),
    )


def _overlap_at_n(
    reference_headings: tuple[str, ...], candidate_headings: tuple[str, ...]
) -> float | None:
    if not reference_headings:
        return None
    intersection = set(reference_headings) & set(candidate_headings)
    return len(intersection) / len(set(reference_headings))
