"""SearchTerm model and term generation (TASK-H008/J002-J005/L005, ARCHITECTURE.md 14.1).

`title_terms_for_article` covers the article's own title (`kind="title"`),
its redirect-sourced aliases (`kind="redirect"`, TASK-H004), and three
variants of each (`kind="alias"`): space-removed (TASK-J002, see
`wikiepwing.search.space_variant`), hiragana/katakana-swapped (TASK-J003,
see `wikiepwing.search.kana_variant`), and punctuation-removed (TASK-J004,
see `wikiepwing.search.punctuation_variant`). `heading_keyword_terms_for_article`
(TASK-Q001) covers heading text; infobox keyword/cross_component terms
remain separate, later work.

`category_terms_for_article` (TASK-L005, `kind="category"`) is
deliberately *not* folded into `title_terms_for_article`'s output: a
category name maps to every article in it (one-to-many), unlike every
other term kind here (one key -> one article, TASK-J006's collision
resolution picks a single winner when two different articles' terms
collide on the same key). Feeding category terms through
`wikiepwing.search.backend_mapping.headwords_for_articles`'s
single-candidate resolution would wrongly collapse a whole category down
to one article's headword. Category terms only make sense once
`rendered.sqlite3`'s `search_terms` table (DATA_CONTRACTS.md 7, no
uniqueness constraint on `normalized_key` by design) has a persistence
layer to hold every candidate; until then this function exists as a
standalone generator callers can use directly.

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
from wikiepwing.model.blocks import Block, HeadingBlock, InfoboxBlock
from wikiepwing.model.inline import Inline
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
_CATEGORY_PRIORITY = 500
_HEADING_KEYWORD_PRIORITY = 400
_INFOBOX_KEYWORD_PRIORITY = 300

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


def category_terms_for_article(article: Article) -> tuple[SearchTerm, ...]:
    """Return one `kind="category"` SearchTerm per category the article belongs to.

    See this module's docstring for why these are generated separately
    from `title_terms_for_article` rather than merged into it.
    """
    return tuple(
        SearchTerm(
            key=category,
            normalized_key=normalize_index_key(category),
            target_page_id=article.page_id,
            kind="category",
            priority=_CATEGORY_PRIORITY,
            source="category",
        )
        for category in article.categories
    )


def heading_keyword_terms_for_article(article: Article) -> tuple[SearchTerm, ...]:
    """Return one `kind="keyword"` SearchTerm per distinct heading text (TASK-Q001).

    Like `category_terms_for_article`, this is deliberately separate from
    `title_terms_for_article`: a heading's text (e.g. "概要") is common
    across many unrelated articles, a one-to-many key unlike title/redirect
    terms.
    """
    terms: list[SearchTerm] = []
    seen_normalized_keys: set[str] = set()
    for block in article.blocks:
        if not isinstance(block, HeadingBlock):
            continue
        text = _flatten_inline_text(block.inlines)
        if not text:
            continue
        normalized_key = normalize_index_key(text)
        if not normalized_key or normalized_key in seen_normalized_keys:
            continue
        seen_normalized_keys.add(normalized_key)
        terms.append(
            SearchTerm(
                key=text,
                normalized_key=normalized_key,
                target_page_id=article.page_id,
                kind="keyword",
                priority=_HEADING_KEYWORD_PRIORITY,
                source="heading",
            )
        )
    return tuple(terms)


def infobox_keyword_terms_for_article(article: Article) -> tuple[SearchTerm, ...]:
    """Return one `kind="keyword"` SearchTerm per distinct infobox field value (TASK-Q002).

    Only field *values* are extracted, not their names/labels (a label
    like "生年月日" is a generic column heading, not a searchable term).
    Deduplicated and kept separate from `title_terms_for_article` for the
    same one-to-many reason as `category_terms_for_article`/
    `heading_keyword_terms_for_article`.
    """
    terms: list[SearchTerm] = []
    seen_normalized_keys: set[str] = set()
    for block in article.blocks:
        if not isinstance(block, InfoboxBlock):
            continue
        for field in block.fields:
            text = _flatten_block_text(field.value)
            if not text:
                continue
            normalized_key = normalize_index_key(text)
            if not normalized_key or normalized_key in seen_normalized_keys:
                continue
            seen_normalized_keys.add(normalized_key)
            terms.append(
                SearchTerm(
                    key=text,
                    normalized_key=normalized_key,
                    target_page_id=article.page_id,
                    kind="keyword",
                    priority=_INFOBOX_KEYWORD_PRIORITY,
                    source="infobox",
                )
            )
    return tuple(terms)


def _flatten_block_text(blocks: tuple[Block, ...]) -> str:
    parts: list[str] = []
    for block in blocks:
        inlines = getattr(block, "inlines", None)
        if inlines is not None:
            parts.append(_flatten_inline_text(inlines))
            continue
        nested_blocks = getattr(block, "blocks", None)
        if nested_blocks is not None:
            parts.append(_flatten_block_text(nested_blocks))
    return " ".join(part for part in parts if part).strip()


def _flatten_inline_text(inlines: tuple[Inline, ...]) -> str:
    parts: list[str] = []
    for inline in inlines:
        value = getattr(inline, "value", None)
        if isinstance(value, str):
            parts.append(value)
            continue
        nested = getattr(inline, "inlines", None)
        if nested is not None:
            parts.append(_flatten_inline_text(nested))
    return "".join(parts).strip()


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
