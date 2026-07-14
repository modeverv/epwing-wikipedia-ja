"""SearchTerm collision detection and resolution (TASK-J006, ARCHITECTURE.md 14.2).

14.2's collision rule for a `normalized_key` that resolves to more than one
article: never silently overwrite, prefer a backend that can keep every
candidate, fall back to priority + stable sort (TASK-J005's
`sort_search_terms`) only when a backend can hold a single candidate per
key, and report whatever gets dropped in that fallback.

`rendered.sqlite3` (DATA_CONTRACTS.md 7's `search_terms` table) is the
backend that *can* keep every candidate -- its schema has no uniqueness
constraint on `normalized_key`, by design. That table's persistence layer
does not exist yet (a separate task); this module only implements the pure
collision detection/resolution/report logic so that layer, and any
single-candidate backend, can call it directly.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from wikiepwing.search.search_term import SearchTerm, sort_search_terms


@dataclass(frozen=True, slots=True)
class SearchTermCollision:
    """One `normalized_key` that resolves to more than one distinct article."""

    normalized_key: str
    winner: SearchTerm
    dropped: tuple[SearchTerm, ...]


def find_collisions(terms: Iterable[SearchTerm]) -> tuple[SearchTermCollision, ...]:
    """Report every `normalized_key` group whose terms target more than one article.

    Groups where every term already targets the same `target_page_id` are not
    collisions (e.g. a title and a redirect that happen to normalize alike)
    and are omitted. Within a real collision, the winner is the term
    `sort_search_terms` ranks first for that key.
    """
    collisions = []
    for normalized_key, group in _group_by_normalized_key(terms).items():
        target_page_ids = {term.target_page_id for term in group}
        if len(target_page_ids) <= 1:
            continue
        ordered = sort_search_terms(group)
        collisions.append(
            SearchTermCollision(
                normalized_key=normalized_key, winner=ordered[0], dropped=ordered[1:]
            )
        )
    return tuple(sorted(collisions, key=lambda collision: collision.normalized_key))


def resolve_single_candidate_per_key(terms: Iterable[SearchTerm]) -> tuple[SearchTerm, ...]:
    """Return one SearchTerm per `normalized_key`, for backends without J006's full storage.

    Within each `normalized_key` group (whether or not it is a real
    collision), the surviving term is the one `sort_search_terms` ranks
    first.
    """
    winners = [sort_search_terms(group)[0] for group in _group_by_normalized_key(terms).values()]
    return tuple(sort_search_terms(winners))


def _group_by_normalized_key(terms: Iterable[SearchTerm]) -> dict[str, list[SearchTerm]]:
    groups: dict[str, list[SearchTerm]] = defaultdict(list)
    for term in terms:
        groups[term.normalized_key].append(term)
    return groups
