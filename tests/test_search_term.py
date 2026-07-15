from __future__ import annotations

from datetime import UTC, datetime

import pytest

from wikiepwing.model.article import Alias, Article
from wikiepwing.model.blocks import HeadingBlock, ParagraphBlock
from wikiepwing.model.inline import StrongInline, TextInline
from wikiepwing.search.search_term import (
    SearchTerm,
    SearchTermError,
    category_terms_for_article,
    cross_component_terms_for_article,
    heading_keyword_terms_for_article,
    infobox_keyword_terms_for_article,
    lead_alias_terms_for_article,
    sort_search_terms,
    title_terms_for_article,
)


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

    assert terms[0].priority > terms[1].priority


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


def test_kana_title_gets_a_kana_swapped_variant() -> None:
    article = _make_article(title="ひらがな", normalized_title="ひらがな")

    terms = title_terms_for_article(article)

    variants = [term for term in terms if term.source == "kana_variant"]
    assert len(variants) == 1
    assert variants[0].normalized_key == "ヒラガナ"
    assert variants[0].kind == "alias"


def test_non_kana_title_gets_no_kana_variant() -> None:
    article = _make_article()

    terms = title_terms_for_article(article)

    assert not any(term.source == "kana_variant" for term in terms)


def test_kana_redirect_alias_also_gets_a_kana_swapped_variant() -> None:
    article = _make_article(aliases=(Alias(title="カタカナ", source="redirect", confidence=1.0),))

    terms = title_terms_for_article(article)

    variants = [term for term in terms if term.source == "kana_variant"]
    assert len(variants) == 1
    assert variants[0].normalized_key == "かたかな"


def test_title_with_middle_dot_gets_a_punctuation_removed_variant() -> None:
    article = _make_article(title="スター・ウォーズ", normalized_title="スター・ウォーズ")

    terms = title_terms_for_article(article)

    variants = [term for term in terms if term.source == "punctuation_variant"]
    assert len(variants) == 1
    assert variants[0].normalized_key == "スターウォーズ"
    assert variants[0].kind == "alias"


def test_title_without_punctuation_gets_no_punctuation_variant() -> None:
    article = _make_article()

    terms = title_terms_for_article(article)

    assert not any(term.source == "punctuation_variant" for term in terms)


def test_priorities_follow_data_contracts_scale() -> None:
    article = _make_article(
        title="GNU Emacs",
        normalized_title="GNU Emacs",
        aliases=(Alias(title="ひらがな エディタ", source="redirect", confidence=1.0),),
    )

    terms = title_terms_for_article(article)
    by_source = {term.source: term.priority for term in terms}

    assert by_source["normalize"] == 1000
    assert by_source["redirect"] == 900
    assert by_source["nfkc_case_space_variant"] == 800
    assert by_source["kana_variant"] == 600


def _term(priority: int, normalized_key: str, page_id: int = 1, source: str = "s") -> SearchTerm:
    return SearchTerm(
        key=normalized_key,
        normalized_key=normalized_key,
        target_page_id=page_id,
        kind="alias",
        priority=priority,
        source=source,
    )


def test_sort_search_terms_orders_by_priority_descending() -> None:
    low = _term(100, "a")
    high = _term(900, "b")

    assert sort_search_terms([low, high]) == (high, low)


def test_sort_search_terms_tie_breaks_by_normalized_key_then_page_id_then_source() -> None:
    a = _term(500, "b", page_id=2, source="z")
    b = _term(500, "a", page_id=1, source="a")
    c = _term(500, "a", page_id=1, source="b")

    assert sort_search_terms([a, b, c]) == (b, c, a)


def test_category_terms_generate_one_term_per_category() -> None:
    article = _make_article(categories=("Text editors", "Free software"))

    terms = category_terms_for_article(article)

    assert len(terms) == 2
    assert {term.key for term in terms} == {"Text editors", "Free software"}
    assert all(term.kind == "category" for term in terms)
    assert all(term.priority == 500 for term in terms)
    assert all(term.target_page_id == article.page_id for term in terms)
    assert all(term.source == "category" for term in terms)


def test_category_terms_use_normalized_index_key() -> None:
    article = _make_article(categories=("Ｅｍａｃｓ",))

    terms = category_terms_for_article(article)

    assert terms[0].normalized_key == "emacs"


def test_no_categories_yields_no_category_terms() -> None:
    article = _make_article()

    assert category_terms_for_article(article) == ()


def test_category_terms_are_not_part_of_title_terms_for_article() -> None:
    article = _make_article(categories=("Text editors",))

    terms = title_terms_for_article(article)

    assert not any(term.kind == "category" for term in terms)


def test_heading_keyword_terms_extracted_from_heading_blocks() -> None:
    article = _make_article(
        blocks=(
            HeadingBlock(level=2, anchor="overview", inlines=(TextInline(value="概要"),)),
            ParagraphBlock(inlines=(TextInline(value="body text"),)),
        )
    )

    terms = heading_keyword_terms_for_article(article)

    assert len(terms) == 1
    assert terms[0].key == "概要"
    assert terms[0].kind == "keyword"
    assert terms[0].priority == 400
    assert terms[0].source == "heading"
    assert terms[0].target_page_id == article.page_id


def test_heading_keyword_terms_flatten_nested_inlines() -> None:
    article = _make_article(
        blocks=(
            HeadingBlock(
                level=2,
                anchor="h",
                inlines=(StrongInline(inlines=(TextInline(value="Bold Heading"),)),),
            ),
        )
    )

    terms = heading_keyword_terms_for_article(article)

    assert terms[0].key == "Bold Heading"


def test_heading_keyword_terms_deduplicate_by_normalized_key() -> None:
    article = _make_article(
        blocks=(
            HeadingBlock(level=2, anchor="a", inlines=(TextInline(value="概要"),)),
            HeadingBlock(level=3, anchor="b", inlines=(TextInline(value="概要"),)),
        )
    )

    terms = heading_keyword_terms_for_article(article)

    assert len(terms) == 1


def test_heading_keyword_terms_ignore_empty_headings() -> None:
    article = _make_article(blocks=(HeadingBlock(level=2, anchor="a", inlines=()),))

    terms = heading_keyword_terms_for_article(article)

    assert terms == ()


def test_no_headings_yields_no_heading_keyword_terms() -> None:
    article = _make_article(blocks=(ParagraphBlock(inlines=(TextInline(value="text"),)),))

    assert heading_keyword_terms_for_article(article) == ()


def test_heading_keyword_terms_use_normalized_index_key() -> None:
    article = _make_article(
        blocks=(HeadingBlock(level=2, anchor="a", inlines=(TextInline(value="Ｅｍａｃｓ"),)),)
    )

    terms = heading_keyword_terms_for_article(article)

    assert terms[0].normalized_key == "emacs"


def test_infobox_keyword_terms_extracted_from_field_values() -> None:
    from wikiepwing.model.blocks import InfoboxBlock, InfoboxField

    article = _make_article(
        blocks=(
            InfoboxBlock(
                title="Emacs",
                fields=(
                    InfoboxField(
                        name="Developer",
                        value=(ParagraphBlock(inlines=(TextInline(value="GNU Project"),)),),
                    ),
                ),
                images=(),
            ),
        )
    )

    terms = infobox_keyword_terms_for_article(article)

    assert len(terms) == 1
    assert terms[0].key == "GNU Project"
    assert terms[0].kind == "keyword"
    assert terms[0].priority == 300
    assert terms[0].source == "infobox"
    assert terms[0].target_page_id == article.page_id


def test_infobox_keyword_terms_exclude_field_names() -> None:
    from wikiepwing.model.blocks import InfoboxBlock, InfoboxField

    article = _make_article(
        blocks=(
            InfoboxBlock(
                title=None,
                fields=(
                    InfoboxField(
                        name="Developer",
                        value=(ParagraphBlock(inlines=(TextInline(value="GNU Project"),)),),
                    ),
                ),
                images=(),
            ),
        )
    )

    terms = infobox_keyword_terms_for_article(article)

    assert all(term.key != "Developer" for term in terms)


def test_infobox_keyword_terms_deduplicate_by_normalized_key() -> None:
    from wikiepwing.model.blocks import InfoboxBlock, InfoboxField

    article = _make_article(
        blocks=(
            InfoboxBlock(
                title=None,
                fields=(
                    InfoboxField(
                        name="A",
                        value=(ParagraphBlock(inlines=(TextInline(value="GNU Project"),)),),
                    ),
                    InfoboxField(
                        name="B",
                        value=(ParagraphBlock(inlines=(TextInline(value="GNU Project"),)),),
                    ),
                ),
                images=(),
            ),
        )
    )

    terms = infobox_keyword_terms_for_article(article)

    assert len(terms) == 1


def test_infobox_keyword_terms_ignore_empty_field_values() -> None:
    from wikiepwing.model.blocks import InfoboxBlock, InfoboxField

    article = _make_article(
        blocks=(InfoboxBlock(title=None, fields=(InfoboxField(name="A", value=()),), images=()),)
    )

    terms = infobox_keyword_terms_for_article(article)

    assert terms == ()


def test_no_infobox_yields_no_infobox_keyword_terms() -> None:
    article = _make_article(blocks=(ParagraphBlock(inlines=(TextInline(value="text"),)),))

    assert infobox_keyword_terms_for_article(article) == ()


def test_lead_alias_terms_extracted_from_bold_span_in_first_paragraph() -> None:
    article = _make_article(
        title="GNU Emacs",
        blocks=(
            ParagraphBlock(
                inlines=(
                    TextInline(value="also known as "),
                    StrongInline(inlines=(TextInline(value="Emacs"),)),
                    TextInline(value="."),
                )
            ),
        ),
    )

    terms = lead_alias_terms_for_article(article)

    assert len(terms) == 1
    assert terms[0].key == "Emacs"
    assert terms[0].kind == "alias"
    assert terms[0].priority == 200
    assert terms[0].source == "lead"
    assert terms[0].target_page_id == article.page_id


def test_lead_alias_terms_ignore_paragraphs_after_a_heading() -> None:
    article = _make_article(
        blocks=(
            HeadingBlock(level=2, anchor="h", inlines=(TextInline(value="概要"),)),
            ParagraphBlock(inlines=(StrongInline(inlines=(TextInline(value="Emacs"),)),)),
        ),
    )

    terms = lead_alias_terms_for_article(article)

    assert terms == ()


def test_lead_alias_terms_exclude_bold_span_matching_the_title() -> None:
    article = _make_article(
        title="Emacs",
        blocks=(ParagraphBlock(inlines=(StrongInline(inlines=(TextInline(value="Emacs"),)),)),),
    )

    terms = lead_alias_terms_for_article(article)

    assert terms == ()


def test_lead_alias_terms_deduplicate_by_normalized_key() -> None:
    article = _make_article(
        title="GNU Emacs",
        blocks=(
            ParagraphBlock(
                inlines=(
                    StrongInline(inlines=(TextInline(value="Emacs"),)),
                    TextInline(value=" "),
                    StrongInline(inlines=(TextInline(value="Emacs"),)),
                )
            ),
        ),
    )

    terms = lead_alias_terms_for_article(article)

    assert len(terms) == 1


def test_lead_alias_terms_no_bold_spans_yields_empty() -> None:
    article = _make_article(blocks=(ParagraphBlock(inlines=(TextInline(value="plain text"),)),))

    assert lead_alias_terms_for_article(article) == ()


def test_lead_alias_terms_no_paragraph_yields_empty() -> None:
    article = _make_article(
        blocks=(HeadingBlock(level=2, anchor="h", inlines=(TextInline(value="概要"),)),),
    )

    assert lead_alias_terms_for_article(article) == ()


def test_lead_alias_terms_no_blocks_yields_empty() -> None:
    article = _make_article()

    assert lead_alias_terms_for_article(article) == ()


def test_cross_component_terms_split_multi_word_title() -> None:
    article = _make_article(title="GNU Emacs")

    terms = cross_component_terms_for_article(article)

    keys = {term.key for term in terms}
    assert keys == {"GNU", "Emacs"}
    assert all(term.kind == "cross_component" for term in terms)
    assert all(term.priority == 100 for term in terms)
    assert all(term.source == "cross_component" for term in terms)
    assert all(term.target_page_id == article.page_id for term in terms)


def test_cross_component_terms_single_word_title_yields_nothing() -> None:
    article = _make_article(title="Emacs")

    assert cross_component_terms_for_article(article) == ()


def test_cross_component_terms_include_redirect_alias_components() -> None:
    article = _make_article(
        title="Emacs",
        aliases=(Alias(title="Text Editor", source="redirect", confidence=1.0),),
    )

    terms = cross_component_terms_for_article(article)

    keys = {term.key for term in terms}
    assert keys == {"Text", "Editor"}


def test_cross_component_terms_exclude_non_redirect_alias_components() -> None:
    article = _make_article(
        title="Emacs",
        aliases=(Alias(title="Text Editor", source="wikidata", confidence=0.5),),
    )

    assert cross_component_terms_for_article(article) == ()


def test_cross_component_terms_deduplicate_by_normalized_key() -> None:
    article = _make_article(
        title="Emacs Editor",
        aliases=(Alias(title="Editor Emacs", source="redirect", confidence=1.0),),
    )

    terms = cross_component_terms_for_article(article)

    assert len(terms) == 2
