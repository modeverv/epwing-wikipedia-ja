from __future__ import annotations

from datetime import UTC, datetime

from wikiepwing.model.article import Alias, Article
from wikiepwing.search.backend_mapping import headwords_for_articles


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


def test_single_article_gets_its_own_title_and_redirect_as_headwords() -> None:
    article = _make_article(aliases=(Alias(title="GNU Emacs", source="redirect", confidence=1.0),))

    headwords = headwords_for_articles([article])

    assert headwords[1][0] == "Emacs"
    assert "GNU Emacs" in headwords[1]


def test_two_unrelated_articles_each_keep_their_own_headwords() -> None:
    emacs = _make_article(page_id=1, title="Emacs")
    linux = _make_article(page_id=2, title="Linux")

    headwords = headwords_for_articles([emacs, linux])

    assert headwords[1] == ("Emacs",)
    assert headwords[2] == ("Linux",)


def test_colliding_variant_is_preserved_for_both_articles_with_duplicate_headwords_allowed() -> (
    None
):
    # Both articles' titles or aliases produce the same space-removed variant key
    # ("newyork"). Because FreePWING supports duplicate headwords across entries,
    # both articles keep that headword.
    new_york = _make_article(page_id=1, title="New York")
    other = _make_article(
        page_id=2,
        title="Other Place",
        aliases=(Alias(title="New York", source="redirect", confidence=1.0),),
    )

    headwords = headwords_for_articles([new_york, other])

    assert "newyork" in headwords[1]
    assert "newyork" in headwords[2]
    assert headwords[2][0] == "Other Place"


def test_every_article_keeps_at_least_its_own_title() -> None:
    article = _make_article(page_id=1, title="Emacs")

    headwords = headwords_for_articles([article])

    assert "Emacs" in headwords[1]
