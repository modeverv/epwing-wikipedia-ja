"""Backend search mapping: Articles -> per-article headword lists (TASK-J007).

Ties together the SearchTerm pipeline (TASK-H008, TASK-J001-J006) with the
FreePWING/EB backend, which -- like `wikiepwing.render.verify`'s
DUPLICATE_HEADWORD check already enforces -- can only assign one literal
headword string to one entry. That is exactly
`wikiepwing.search.collision.resolve_single_candidate_per_key`'s contract,
so this module: generates every SearchTerm (title, redirect, and
space/kana/punctuation variants) across *all* articles being built,
resolves any cross-article collisions globally, then regroups the
surviving terms back by `target_page_id` in priority order for
`wikiepwing.render.mini_layout.render_article_to_entry` to use as headwords.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from wikiepwing.model.article import Article
from wikiepwing.search.collision import resolve_single_candidate_per_key
from wikiepwing.search.search_term import sort_search_terms, title_terms_for_article


def headwords_for_articles(articles: Iterable[Article]) -> dict[int, tuple[str, ...]]:
    """Return each article's `page_id` mapped to its final, collision-resolved headwords.

    Highest-priority headword first (ARCHITECTURE.md 14.1's `priority`); an
    article that lost every one of its terms to higher-priority collisions
    from other articles still keeps its own title as a last resort, so
    every entry has at least one headword.
    """
    articles = tuple(articles)
    all_terms = [term for article in articles for term in title_terms_for_article(article)]
    resolved = resolve_single_candidate_per_key(all_terms)

    by_page_id: dict[int, list[str]] = defaultdict(list)
    for term in sort_search_terms(resolved):
        by_page_id[term.target_page_id].append(term.key)

    headwords: dict[int, tuple[str, ...]] = {}
    for article in articles:
        keys = by_page_id.get(article.page_id, [])
        if article.title not in keys:
            keys = [article.title, *keys]
        headwords[article.page_id] = tuple(keys)
    return headwords
