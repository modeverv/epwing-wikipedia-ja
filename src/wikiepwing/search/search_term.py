"""SearchTerm model and title/redirect term generation (TASK-H008/J002/J003, ARCHITECTURE.md 14.1).

`title_terms_for_article` covers the article's own title (`kind="title"`),
its redirect-sourced aliases (`kind="redirect"`, TASK-H004), a
space-removed variant of each (`kind="alias"`, TASK-J002 -- see
`wikiepwing.search.space_variant`), and a hiragana/katakana-swapped variant
of each (`kind="alias"`, TASK-J003 -- see `wikiepwing.search.kana_variant`).
reading/category/keyword/cross_component terms are separate, later work,
as are the collision rules (14.2) and per-profile indexing (14.3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from wikiepwing.model.article import Article
from wikiepwing.search.kana_variant import kana_variant
from wikiepwing.search.normalize_key import normalize_index_key
from wikiepwing.search.space_variant import space_removed_variant

SearchTermKind = Literal[
    "title", "redirect", "alias", "reading", "category", "keyword", "cross_component"
]
_KINDS = ("title", "redirect", "alias", "reading", "category", "keyword", "cross_component")

_TITLE_PRIORITY = 0
_REDIRECT_PRIORITY = 10
_SPACE_VARIANT_PRIORITY = 20
_KANA_VARIANT_PRIORITY = 30


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
    """Return the title, redirect-alias, space-removed, and kana-swapped variant SearchTerms."""
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


def _variant_terms(normalized_key: str, page_id: int) -> tuple[SearchTerm, ...]:
    variants: list[SearchTerm] = []
    space_variant = space_removed_variant(normalized_key)
    if space_variant is not None:
        variants.append(
            SearchTerm(
                key=space_variant,
                normalized_key=space_variant,
                target_page_id=page_id,
                kind="alias",
                priority=_SPACE_VARIANT_PRIORITY,
                source="nfkc_case_space_variant",
            )
        )
    kana_swapped = kana_variant(normalized_key)
    if kana_swapped is not None:
        variants.append(
            SearchTerm(
                key=kana_swapped,
                normalized_key=kana_swapped,
                target_page_id=page_id,
                kind="alias",
                priority=_KANA_VARIANT_PRIORITY,
                source="kana_variant",
            )
        )
    return tuple(variants)
