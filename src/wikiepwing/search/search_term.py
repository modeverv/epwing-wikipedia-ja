"""SearchTerm model and title/redirect term generation (TASK-H008/J002-J005, ARCHITECTURE.md 14.1).

`title_terms_for_article` covers the article's own title (`kind="title"`),
its redirect-sourced aliases (`kind="redirect"`, TASK-H004), and three
variants of each (`kind="alias"`): space-removed (TASK-J002, see
`wikiepwing.search.space_variant`), hiragana/katakana-swapped (TASK-J003,
see `wikiepwing.search.kana_variant`), and punctuation-removed (TASK-J004,
see `wikiepwing.search.punctuation_variant`). reading/category/keyword/
cross_component terms are separate, later work (no code generates them
yet), as is the collision repository/report (TASK-J006).

Priorities (TASK-J005) follow DATA_CONTRACTS.md 8's proposal, where a
*higher* number wins. `sort_search_terms` applies its priority-descending
order plus the specified `normalized_key`/`target_page_id`/`source`
stable tie-break for same-priority collisions (14.2).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal

from wikiepwing.model.article import Article
from wikiepwing.search.kana_variant import kana_variant
from wikiepwing.search.normalize_key import normalize_index_key
from wikiepwing.search.punctuation_variant import punctuation_removed_variant
from wikiepwing.search.space_variant import space_removed_variant

SearchTermKind = Literal[
    "title", "redirect", "alias", "reading", "category", "keyword", "cross_component"
]
_KINDS = ("title", "redirect", "alias", "reading", "category", "keyword", "cross_component")

# DATA_CONTRACTS.md 8 priority proposal (higher wins): 1000 exact title,
# 900 original redirect, 800 normalized title variant, 700 explicit alias,
# 600 kana variant, 500 category, 400 heading keyword, 300 infobox keyword,
# 200 lead term, 100 cross component.
_TITLE_PRIORITY = 1000
_REDIRECT_PRIORITY = 900
_NORMALIZED_TITLE_VARIANT_PRIORITY = 800
_KANA_VARIANT_PRIORITY = 600

_VARIANT_GENERATORS: tuple[tuple[Callable[[str], str | None], int, str], ...] = (
    (space_removed_variant, _NORMALIZED_TITLE_VARIANT_PRIORITY, "nfkc_case_space_variant"),
    (kana_variant, _KANA_VARIANT_PRIORITY, "kana_variant"),
    (punctuation_removed_variant, _NORMALIZED_TITLE_VARIANT_PRIORITY, "punctuation_variant"),
)


class SearchTermError(ValueError):
    """Raised when a SearchTerm cannot be constructed safely."""


@dataclass(frozen=True, slots=True)
class SearchTerm:
    """One search index entry (ARCHITECTURE.md 14.1)."""

    key: str
    normalized_key: str
    target_page_id: int
    kind: SearchTermKind
    priority: int
    source: str

    def __post_init__(self) -> None:
        if not self.key:
            raise SearchTermError("key must be a non-empty string")
        if not self.normalized_key:
            raise SearchTermError("normalized_key must be a non-empty string")
        if not self.source:
            raise SearchTermError("source must be a non-empty string")
        if self.target_page_id < 1:
            raise SearchTermError(f"target_page_id must be positive: {self.target_page_id!r}")
        if self.kind not in _KINDS:
            raise SearchTermError(f"kind must be one of {_KINDS}: {self.kind!r}")


def title_terms_for_article(article: Article) -> tuple[SearchTerm, ...]:
    """Return the title, redirect-alias, and space/kana/punctuation variant SearchTerms."""
    title_normalized_key = normalize_index_key(article.title)
    terms = [
        SearchTerm(
            key=article.title,
            normalized_key=title_normalized_key,
            target_page_id=article.page_id,
            kind="title",
            priority=_TITLE_PRIORITY,
            source="normalize",
        )
    ]
    terms.extend(_variant_terms(title_normalized_key, article.page_id))
    for alias in article.aliases:
        if alias.source != "redirect":
            continue
        alias_normalized_key = normalize_index_key(alias.title)
        terms.append(
            SearchTerm(
                key=alias.title,
                normalized_key=alias_normalized_key,
                target_page_id=article.page_id,
                kind="redirect",
                priority=_REDIRECT_PRIORITY,
                source="redirect",
            )
        )
        terms.extend(_variant_terms(alias_normalized_key, article.page_id))
    return tuple(terms)


def sort_search_terms(terms: Iterable[SearchTerm]) -> tuple[SearchTerm, ...]:
    """Order SearchTerms by priority (highest first), tie-broken per DATA_CONTRACTS.md 8.

    Same-priority collisions are broken by `normalized_key`, then
    `target_page_id`, then `source`, all ascending, for a deterministic order.
    """
    return tuple(
        sorted(
            terms,
            key=lambda term: (
                -term.priority,
                term.normalized_key,
                term.target_page_id,
                term.source,
            ),
        )
    )


def _variant_terms(normalized_key: str, page_id: int) -> tuple[SearchTerm, ...]:
    variants: list[SearchTerm] = []
    for generate, priority, source in _VARIANT_GENERATORS:
        variant = generate(normalized_key)
        if variant is None:
            continue
        variants.append(
            SearchTerm(
                key=variant,
                normalized_key=variant,
                target_page_id=page_id,
                kind="alias",
                priority=priority,
                source=source,
            )
        )
    return tuple(variants)
