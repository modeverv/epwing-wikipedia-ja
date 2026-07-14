from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from wikiepwing.model.article import (
    Alias,
    Article,
    ArticleError,
    MediaReference,
    parse_alias,
    parse_article,
    parse_media_reference,
)
from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import TextInline


def _make_article(**overrides: object) -> Article:
    defaults: dict[str, object] = {
        "page_id": 123,
        "revision_id": 456,
        "title": "Emacs",
        "normalized_title": "Emacs",
        "source_url": "https://ja.wikipedia.org/wiki/Emacs",
        "source_date_modified": datetime(2026, 1, 1, tzinfo=UTC),
        "abstract": None,
        "blocks": (),
        "aliases": (),
        "categories": (),
        "media": (),
        "diagnostics": (),
        "source_license_ids": ("CC-BY-SA-3.0",),
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def test_article_round_trips_with_minimal_fields() -> None:
    article = _make_article()

    restored = parse_article(article.payload())

    assert restored == article


def test_article_payload_formats_datetime_as_utc_z_suffix() -> None:
    article = _make_article(source_date_modified=datetime(2026, 1, 1, tzinfo=UTC))

    assert article.payload()["source_date_modified"] == "2026-01-01T00:00:00Z"


def test_article_round_trips_with_non_utc_datetime() -> None:
    jst = timezone(timedelta(hours=9))
    article = _make_article(source_date_modified=datetime(2026, 1, 1, 9, 0, tzinfo=jst))

    restored = parse_article(article.payload())

    assert restored.source_date_modified == article.source_date_modified


def test_article_round_trips_with_nested_blocks_aliases_media_diagnostics() -> None:
    article = _make_article(
        blocks=(ParagraphBlock(inlines=(TextInline("hello"),)),),
        aliases=(Alias(title="GNU Emacs", source="redirect", confidence=0.9),),
        categories=("Text editors",),
        media=(
            MediaReference(
                media_id="File:Emacs.png",
                source_url="https://upload.wikimedia.org/Emacs.png",
                source_name="Emacs.png",
                alt_text="screenshot",
                caption="Emacs running",
                role="lead",
                source_width=640,
                source_height=480,
            ),
        ),
        diagnostics=(
            Diagnostic(
                code="REC_TEST",
                severity="info",
                stage="normalize",
                page_id=123,
                title="Emacs",
                message="test diagnostic",
                source_path=None,
                source_excerpt=None,
                details={},
            ),
        ),
    )

    restored = parse_article(article.payload())

    assert restored == article


def test_article_rejects_empty_title() -> None:
    with pytest.raises(ArticleError, match="title"):
        _make_article(title="")


def test_article_rejects_empty_normalized_title() -> None:
    with pytest.raises(ArticleError, match="normalized_title"):
        _make_article(normalized_title="")


def test_article_rejects_empty_source_url() -> None:
    with pytest.raises(ArticleError, match="source_url"):
        _make_article(source_url="")


def test_article_rejects_naive_datetime() -> None:
    with pytest.raises(ArticleError, match="timezone-aware"):
        _make_article(source_date_modified=datetime(2026, 1, 1))


def test_parse_article_rejects_naive_datetime_string() -> None:
    payload = _make_article().payload()
    payload["source_date_modified"] = "2026-01-01T00:00:00"

    with pytest.raises(ArticleError, match="timezone-aware"):
        parse_article(payload)


def test_parse_article_rejects_invalid_datetime_string() -> None:
    payload = _make_article().payload()
    payload["source_date_modified"] = "not-a-date"

    with pytest.raises(ArticleError, match="ISO-8601"):
        parse_article(payload)


def test_parse_article_rejects_non_object() -> None:
    with pytest.raises(ArticleError, match="JSON object"):
        parse_article(["not", "an", "object"])


def test_alias_round_trips() -> None:
    alias = Alias(title="GNU Emacs", source="wikidata", confidence=0.5)

    restored = parse_alias(alias.payload())

    assert restored == alias
    assert alias.payload() == {"title": "GNU Emacs", "source": "wikidata", "confidence": 0.5}


def test_alias_rejects_empty_title() -> None:
    with pytest.raises(ArticleError, match="title"):
        Alias(title="", source="redirect", confidence=0.5)


def test_alias_rejects_invalid_source() -> None:
    with pytest.raises(ArticleError, match="source"):
        Alias(title="x", source="unknown", confidence=0.5)  # type: ignore[arg-type]


def test_alias_rejects_confidence_out_of_range() -> None:
    with pytest.raises(ArticleError, match="confidence"):
        Alias(title="x", source="redirect", confidence=1.5)


def test_media_reference_round_trips() -> None:
    media = MediaReference(
        media_id="File:X.png",
        source_url="https://example.org/X.png",
        source_name="X.png",
        alt_text=None,
        caption=None,
        role="unknown",
        source_width=None,
        source_height=None,
    )

    restored = parse_media_reference(media.payload())

    assert restored == media


def test_media_reference_rejects_empty_media_id() -> None:
    with pytest.raises(ArticleError, match="media_id"):
        MediaReference(
            media_id="",
            source_url="https://example.org/x.png",
            source_name=None,
            alt_text=None,
            caption=None,
            role="unknown",
            source_width=None,
            source_height=None,
        )


def test_media_reference_rejects_invalid_role() -> None:
    with pytest.raises(ArticleError, match="role"):
        MediaReference(
            media_id="x",
            source_url="https://example.org/x.png",
            source_name=None,
            alt_text=None,
            caption=None,
            role="hero",  # type: ignore[arg-type]
            source_width=None,
            source_height=None,
        )


def test_media_reference_rejects_negative_width() -> None:
    with pytest.raises(ArticleError, match="source_width"):
        MediaReference(
            media_id="x",
            source_url="https://example.org/x.png",
            source_name=None,
            alt_text=None,
            caption=None,
            role="unknown",
            source_width=-1,
            source_height=None,
        )
