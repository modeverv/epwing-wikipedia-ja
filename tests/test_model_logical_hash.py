from __future__ import annotations

from datetime import UTC, datetime

from wikiepwing.model.article import Alias, Article, MediaReference
from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import TextInline
from wikiepwing.model.logical_hash import compute_logical_hash


def _make_article(**overrides: object) -> Article:
    defaults: dict[str, object] = {
        "page_id": 123,
        "revision_id": 456,
        "title": "Emacs",
        "normalized_title": "Emacs",
        "source_url": "https://ja.wikipedia.org/wiki/Emacs",
        "source_date_modified": datetime(2026, 1, 1, tzinfo=UTC),
        "abstract": None,
        "blocks": (ParagraphBlock(inlines=(TextInline("hello"),)),),
        "aliases": (),
        "categories": (),
        "media": (),
        "diagnostics": (),
        "source_license_ids": ("CC-BY-SA-3.0",),
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def test_compute_logical_hash_returns_sha256_hex_digest() -> None:
    article = _make_article()

    digest = compute_logical_hash(article)

    assert len(digest) == 64
    assert all(char in "0123456789abcdef" for char in digest)


def test_compute_logical_hash_is_deterministic() -> None:
    article = _make_article()

    assert compute_logical_hash(article) == compute_logical_hash(article)


def test_compute_logical_hash_is_stable_across_category_order() -> None:
    a = _make_article(categories=("Editors", "Free software"))
    b = _make_article(categories=("Free software", "Editors"))

    assert compute_logical_hash(a) == compute_logical_hash(b)


def test_compute_logical_hash_is_stable_across_source_license_order() -> None:
    a = _make_article(source_license_ids=("CC-BY-SA-3.0", "GFDL"))
    b = _make_article(source_license_ids=("GFDL", "CC-BY-SA-3.0"))

    assert compute_logical_hash(a) == compute_logical_hash(b)


def test_compute_logical_hash_is_stable_across_alias_order() -> None:
    aliases = (
        Alias(title="GNU Emacs", source="redirect", confidence=0.9),
        Alias(title="Emacs Editor", source="wikidata", confidence=0.5),
    )
    a = _make_article(aliases=aliases)
    b = _make_article(aliases=tuple(reversed(aliases)))

    assert compute_logical_hash(a) == compute_logical_hash(b)


def test_compute_logical_hash_is_stable_across_media_order() -> None:
    media = (
        MediaReference(
            media_id="File:A.png",
            source_url="https://example.org/A.png",
            source_name=None,
            alt_text=None,
            caption=None,
            role="unknown",
            source_width=None,
            source_height=None,
        ),
        MediaReference(
            media_id="File:B.png",
            source_url="https://example.org/B.png",
            source_name=None,
            alt_text=None,
            caption=None,
            role="unknown",
            source_width=None,
            source_height=None,
        ),
    )
    a = _make_article(media=media)
    b = _make_article(media=tuple(reversed(media)))

    assert compute_logical_hash(a) == compute_logical_hash(b)


def test_compute_logical_hash_is_stable_across_diagnostic_order() -> None:
    diagnostics = (
        Diagnostic(
            code="A_CODE",
            severity="info",
            stage="normalize",
            page_id=123,
            title="Emacs",
            message="first",
            source_path=None,
            source_excerpt=None,
            details={},
        ),
        Diagnostic(
            code="B_CODE",
            severity="info",
            stage="normalize",
            page_id=123,
            title="Emacs",
            message="second",
            source_path=None,
            source_excerpt=None,
            details={},
        ),
    )
    a = _make_article(diagnostics=diagnostics)
    b = _make_article(diagnostics=tuple(reversed(diagnostics)))

    assert compute_logical_hash(a) == compute_logical_hash(b)


def test_compute_logical_hash_changes_when_block_order_changes() -> None:
    a = _make_article(
        blocks=(
            ParagraphBlock(inlines=(TextInline("first"),)),
            ParagraphBlock(inlines=(TextInline("second"),)),
        )
    )
    b = _make_article(
        blocks=(
            ParagraphBlock(inlines=(TextInline("second"),)),
            ParagraphBlock(inlines=(TextInline("first"),)),
        )
    )

    assert compute_logical_hash(a) != compute_logical_hash(b)


def test_compute_logical_hash_changes_when_content_differs() -> None:
    a = _make_article(title="Emacs")
    b = _make_article(title="Vim")

    assert compute_logical_hash(a) != compute_logical_hash(b)
