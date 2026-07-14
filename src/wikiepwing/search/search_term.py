"""SearchTerm model and title/redirect term generation (TASK-H008, ARCHITECTURE.md 14.1).

`title_terms_for_article` covers only the two term kinds this task scopes:
the article's own title (`kind="title"`) and its redirect-sourced aliases
(`kind="redirect"`, TASK-H004). reading/category/keyword/cross_component
terms are separate, later work, as are the collision rules (14.2) and
per-profile indexing (14.3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from wikiepwing.ingest.repository import normalize_title
from wikiepwing.model.article import Article

SearchTermKind = Literal[
    "title", "redirect", "alias", "reading", "category", "keyword", "cross_component"
]
_KINDS = ("title", "redirect", "alias", "reading", "category", "keyword", "cross_component")

_TITLE_PRIORITY = 0
_REDIRECT_PRIORITY = 10


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
    """Return the title and redirect-alias SearchTerms for one Article."""
    terms = [
        SearchTerm(
            key=article.title,
            normalized_key=normalize_title(article.title),
            target_page_id=article.page_id,
            kind="title",
            priority=_TITLE_PRIORITY,
            source="normalize",
        )
    ]
    for alias in article.aliases:
        if alias.source != "redirect":
            continue
        terms.append(
            SearchTerm(
                key=alias.title,
                normalized_key=normalize_title(alias.title),
                target_page_id=article.page_id,
                kind="redirect",
                priority=_REDIRECT_PRIORITY,
                source="redirect",
            )
        )
    return tuple(terms)
