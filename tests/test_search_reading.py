from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from wikiepwing.model.article import Article
from wikiepwing.model.blocks import HeadingBlock, ParagraphBlock
from wikiepwing.model.inline import TextInline
from wikiepwing.search.reading import reading_for_article


def _article(title: str, paragraphs: tuple[str, ...]) -> Article:
    return Article(
        page_id=1,
        revision_id=1,
        title=title,
        normalized_title=title,
        source_url="https://ja.wikipedia.org/wiki/test",
        source_date_modified=datetime(2026, 1, 1, tzinfo=UTC),
        abstract=None,
        blocks=tuple(
            ParagraphBlock(inlines=(TextInline(value=paragraph),)) for paragraph in paragraphs
        ),
        aliases=(),
        categories=(),
        media=(),
        diagnostics=(),
        source_license_ids=(),
    )


def test_extracts_first_kana_reading_after_base_title() -> None:
    article = _article("日本 (アルバム)", ("『日本』（にほん／にっぽん）はアルバム。",))

    assert reading_for_article(article) == "にほん"


def test_extracts_reading_from_later_lead_paragraph() -> None:
    article = _article("日本 (新聞)", ("注意書き。", "『日本』（にっぽん）は新聞。"))

    assert reading_for_article(article) == "にっぽん"


def test_rejects_non_kana_parenthetical_text() -> None:
    article = _article("日本 (作品)", ("日本（英語: Japan）は作品。",))

    assert reading_for_article(article) is None


def test_does_not_scan_past_first_heading() -> None:
    article = _article("日本 (作品)", ("導入。",))
    article = replace(
        article,
        blocks=(
            *article.blocks,
            HeadingBlock(level=2, anchor="later", inlines=(TextInline(value="後段"),)),
            ParagraphBlock(inlines=(TextInline(value="日本（にほん）は後段。"),)),
        ),
    )

    assert reading_for_article(article) is None
