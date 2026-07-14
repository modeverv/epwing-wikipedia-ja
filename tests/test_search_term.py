from __future__ import annotations

from datetime import UTC, datetime

import pytest

from wikiepwing.model.article import Alias, Article
from wikiepwing.search.search_term import SearchTerm, SearchTermError, title_terms_for_article


def _make_article(**overrides: object) -> Article:
    defaults: dict[str, object] = {
        "page_id": 1,
        "revision_id": 100,
        "title": "Emacs",
        "normalized_title": "Emacs",
        "source_url": "https://ja.wikipedia.org/wiki/Emacs",
        "source_date_modified": datetime(2026, 6, 1, tzinfo=UTC),
        "abstract": None,
        "blocks": (),
        "aliases": (),
        "categories": (),
        "media": (),
        "diagnostics": (),
        "source_license_ids": (),
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def test_search_term_rejects_empty_key() -> None:
    with pytest.raises(SearchTermError, match="key"):
        SearchTerm(
            key="", normalized_key="x", target_page_id=1, kind="title", priority=0, source="s"
        )


def test_search_term_rejects_non_positive_page_id() -> None:
    with pytest.raises(SearchTermError, match="target_page_id"):
        SearchTerm(
            key="x", normalized_key="x", target_page_id=0, kind="title", priority=0, source="s"
        )


def test_search_term_rejects_invalid_kind() -> None:
    with pytest.raises(SearchTermError, match="kind"):
        SearchTerm(
            key="x",
            normalized_key="x",
            target_page_id=1,
            kind="bogus",  # type: ignore[arg-type]
            priority=0,
            source="s",
        )


def test_title_terms_include_article_title() -> None:
    article = _make_article()

    terms = title_terms_for_article(article)

    assert len(terms) == 1
    assert terms[0].key == "Emacs"
    assert terms[0].kind == "title"
    assert terms[0].target_page_id == 1


def test_title_terms_include_redirect_aliases() -> None:
    article = _make_article(
        aliases=(
            Alias(title="GNU Emacs", source="redirect", confidence=1.0),
            Alias(title="Emacs Editor", source="redirect", confidence=1.0),
        )
    )

    terms = title_terms_for_article(article)

    redirect_keys = [term.key for term in terms if term.kind == "redirect"]
    assert redirect_keys == ["GNU Emacs", "Emacs Editor"]


def test_title_terms_exclude_non_redirect_aliases() -> None:
    article = _make_article(
        aliases=(Alias(title="GNU Emacs Wiki Data", source="wikidata", confidence=0.5),)
    )

    terms = title_terms_for_article(article)

    assert len(terms) == 1
    assert terms[0].kind == "title"


def test_title_priority_is_higher_than_redirect_priority() -> None:
    article = _make_article(aliases=(Alias(title="GNU Emacs", source="redirect", confidence=1.0),))

    terms = title_terms_for_article(article)

    assert terms[0].priority < terms[1].priority


def test_multi_word_title_gets_a_space_removed_alias_variant() -> None:
    article = _make_article(title="GNU Emacs", normalized_title="GNU Emacs")

    terms = title_terms_for_article(article)

    variants = [term for term in terms if term.source == "nfkc_case_space_variant"]
    assert len(variants) == 1
    assert variants[0].normalized_key == "gnuemacs"
    assert variants[0].kind == "alias"
    assert variants[0].target_page_id == article.page_id


def test_single_word_title_gets_no_space_variant() -> None:
    article = _make_article()

    terms = title_terms_for_article(article)

    assert not any(term.source == "nfkc_case_space_variant" for term in terms)


def test_multi_word_redirect_alias_also_gets_a_space_removed_variant() -> None:
    article = _make_article(
        aliases=(Alias(title="Emacs Editor", source="redirect", confidence=1.0),)
    )

    terms = title_terms_for_article(article)

    variants = [term for term in terms if term.source == "nfkc_case_space_variant"]
    assert len(variants) == 1
    assert variants[0].normalized_key == "emacseditor"
