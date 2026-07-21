"""Backend search mapping: Articles -> per-article headword lists (TASK-J007/T048).

Ties together the SearchTerm pipeline (TASK-H008, TASK-J001-J005) with the
FreePWING/EB backend. Generates every SearchTerm (title, redirect, and
space/kana/punctuation variants) across all articles being built.
FreePWING natively supports duplicate headwords across entries (different
articles can share the same headword string, e.g. "日本"), so terms are
grouped by target article, preserving priority order while deduplicating
within each individual article. Every entry keeps its own title as its first headword.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable

from wikiepwing.model.article import Article
from wikiepwing.search.search_term import SearchTerm, sort_search_terms, title_terms_for_article


def headwords_for_articles(
    articles: Iterable[Article],
    *,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> dict[int, tuple[str, ...]]:
    """Return each article's `page_id` mapped to its final headwords.

    Highest-priority headword first (ARCHITECTURE.md 14.1's `priority`); preserves
    all valid titles, redirects, and variants per article without dropping terms when
    another article has a matching headword. Within each article, headwords are
    deduplicated while preserving order. Each article's main title is guaranteed
    to be its first headword.
    """
    articles = tuple(articles)
    all_terms: list[SearchTerm] = []
    for index, article in enumerate(articles, start=1):
        all_terms.extend(title_terms_for_article(article))
        if on_progress is not None:
            on_progress("terms", index, len(articles))

    by_page_id: dict[int, list[str]] = defaultdict(list)
    for term in sort_search_terms(all_terms):
        if term.key not in by_page_id[term.target_page_id]:
            by_page_id[term.target_page_id].append(term.key)

    headwords: dict[int, tuple[str, ...]] = {}
    for index, article in enumerate(articles, start=1):
        keys = by_page_id.get(article.page_id, [])
        if not keys or keys[0] != article.title:
            if article.title in keys:
                keys.remove(article.title)
            keys = [article.title, *keys]
        headwords[article.page_id] = tuple(keys)
        if on_progress is not None:
            on_progress("group", index, len(articles))
    return headwords
