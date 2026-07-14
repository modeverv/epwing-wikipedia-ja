from __future__ import annotations

from wikiepwing.search.collision import find_collisions, resolve_single_candidate_per_key
from wikiepwing.search.search_term import SearchTerm


def _term(normalized_key: str, target_page_id: int, priority: int, source: str = "s") -> SearchTerm:
    return SearchTerm(
        key=normalized_key,
        normalized_key=normalized_key,
        target_page_id=target_page_id,
        kind="alias",
        priority=priority,
        source=source,
    )


def test_no_collision_when_all_terms_share_one_key() -> None:
    terms = [_term("emacs", 1, 1000, "normalize")]

    assert find_collisions(terms) == ()


def test_no_collision_when_same_key_targets_the_same_article() -> None:
    # A title and a redirect that happen to normalize alike -- same article,
    # not a real collision.
    title = _term("emacs", 1, 1000, "normalize")
    redirect = _term("emacs", 1, 900, "redirect")

    assert find_collisions([title, redirect]) == ()


def test_collision_reported_when_same_key_targets_different_articles() -> None:
    winner = _term("mercury", 1, 1000, "normalize")
    loser = _term("mercury", 2, 900, "redirect")

    collisions = find_collisions([winner, loser])

    assert len(collisions) == 1
    assert collisions[0].normalized_key == "mercury"
    assert collisions[0].winner == winner
    assert collisions[0].dropped == (loser,)


def test_higher_priority_term_wins_the_collision() -> None:
    low_priority = _term("mercury", 2, 100)
    high_priority = _term("mercury", 1, 900)

    collisions = find_collisions([low_priority, high_priority])

    assert collisions[0].winner.target_page_id == 1
    assert collisions[0].dropped == (low_priority,)


def test_collisions_are_ordered_by_normalized_key() -> None:
    z_collision = [_term("zebra", 1, 900), _term("zebra", 2, 100)]
    a_collision = [_term("apple", 1, 900), _term("apple", 2, 100)]

    collisions = find_collisions([*z_collision, *a_collision])

    assert [collision.normalized_key for collision in collisions] == ["apple", "zebra"]


def test_resolve_single_candidate_per_key_keeps_only_the_winner() -> None:
    terms = [
        _term("mercury", 1, 1000),
        _term("mercury", 2, 500),
        _term("venus", 3, 1000),
    ]

    resolved = resolve_single_candidate_per_key(terms)

    by_key = {term.normalized_key: term.target_page_id for term in resolved}
    assert by_key == {"mercury": 1, "venus": 3}


def test_resolve_single_candidate_per_key_is_a_no_op_without_collisions() -> None:
    terms = [_term("mercury", 1, 1000), _term("venus", 3, 900)]

    resolved = resolve_single_candidate_per_key(terms)

    assert set(resolved) == set(terms)
