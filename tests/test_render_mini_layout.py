from __future__ import annotations

from datetime import UTC, datetime

from wikiepwing.model.article import Alias, Article
from wikiepwing.model.blocks import (
    HeadingBlock,
    HorizontalRuleBlock,
    InfoboxBlock,
    InfoboxField,
    ListItem,
    ParagraphBlock,
    PreformattedBlock,
    ReferencesBlock,
    TableBlock,
    TableCell,
    UnorderedListBlock,
    UnsupportedBlock,
)
from wikiepwing.model.inline import InternalLinkInline, TextInline
from wikiepwing.render.entry_id import compute_entry_id
from wikiepwing.render.mini_layout import render_article_to_entry
from wikiepwing.render.render_node import TextRenderNode


def _make_article(**overrides: object) -> Article:
    defaults: dict[str, object] = {
        "page_id": 1,
        "revision_id": 100,
        "title": "Emacs",
        "normalized_title": "Emacs",
        "source_url": "https://ja.wikipedia.org/wiki/Emacs",
        "source_date_modified": datetime(2026, 6, 1, tzinfo=UTC),
        "abstract": "An extensible editor.",
        "blocks": (),
        "aliases": (),
        "categories": (),
        "media": (),
        "diagnostics": (),
        "source_license_ids": (),
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def test_entry_id_matches_compute_entry_id() -> None:
    article = _make_article()

    entry = render_article_to_entry(article)

    assert entry.entry_id == compute_entry_id(1)
    assert entry.page_id == 1


def test_body_includes_title_update_date_and_abstract() -> None:
    article = _make_article()

    entry = render_article_to_entry(article)

    assert len(entry.body) == 1
    body_node = entry.body[0]
    assert isinstance(body_node, TextRenderNode)
    lines = body_node.text.split("\n")
    assert lines[0] == "Emacs"
    assert lines[1] == "更新: 2026-06-01"
    assert "An extensible editor." in lines


def test_headwords_include_title_and_aliases() -> None:
    article = _make_article(aliases=(Alias(title="GNU Emacs", source="redirect", confidence=1.0),))

    entry = render_article_to_entry(article)

    assert entry.headwords == ("Emacs", "GNU Emacs")
    body_node = entry.body[0]
    assert isinstance(body_node, TextRenderNode)
    assert "別名: GNU Emacs" in body_node.text


def test_headings_are_numbered_with_sibling_and_nesting_rules() -> None:
    article = _make_article(
        blocks=(
            HeadingBlock(level=2, anchor="a", inlines=(TextInline(value="History"),)),
            HeadingBlock(level=3, anchor="b", inlines=(TextInline(value="Early"),)),
            HeadingBlock(level=3, anchor="c", inlines=(TextInline(value="Later"),)),
            HeadingBlock(level=2, anchor="d", inlines=(TextInline(value="Legacy"),)),
        )
    )

    entry = render_article_to_entry(article)

    body_node = entry.body[0]
    assert isinstance(body_node, TextRenderNode)
    text = body_node.text
    assert "1 History" in text
    assert "1.1 Early" in text
    assert "1.2 Later" in text
    assert "2 Legacy" in text


def test_categories_and_source_license_ids_are_included() -> None:
    article = _make_article(categories=("Text editors",), source_license_ids=("CC-BY-SA-3.0",))

    entry = render_article_to_entry(article)

    body_node = entry.body[0]
    assert isinstance(body_node, TextRenderNode)
    assert "カテゴリ" in body_node.text
    assert "Text editors" in body_node.text
    assert "出典情報" in body_node.text
    assert "CC-BY-SA-3.0" in body_node.text


def test_unordered_list_and_horizontal_rule_render() -> None:
    article = _make_article(
        blocks=(
            UnorderedListBlock(
                items=(ListItem(blocks=(ParagraphBlock(inlines=(TextInline(value="item"),)),)),)
            ),
            HorizontalRuleBlock(),
        )
    )

    entry = render_article_to_entry(article)

    body_node = entry.body[0]
    assert isinstance(body_node, TextRenderNode)
    assert "- item" in body_node.text
    assert "----" in body_node.text


def test_preformatted_block_preserves_lines() -> None:
    article = _make_article(blocks=(PreformattedBlock(text="line one\nline two"),))

    entry = render_article_to_entry(article)

    body_node = entry.body[0]
    assert isinstance(body_node, TextRenderNode)
    assert "line one" in body_node.text
    assert "line two" in body_node.text


def test_unsupported_block_fallback_text_is_included() -> None:
    article = _make_article(
        blocks=(
            UnsupportedBlock(
                element_name="table", fallback_text="cell content", diagnostic_code="X"
            ),
        )
    )

    entry = render_article_to_entry(article)

    body_node = entry.body[0]
    assert isinstance(body_node, TextRenderNode)
    assert "cell content" in body_node.text


def test_estimated_size_matches_utf8_byte_length() -> None:
    article = _make_article()

    entry = render_article_to_entry(article)

    body_node = entry.body[0]
    assert isinstance(body_node, TextRenderNode)
    assert entry.estimated_size == len(body_node.text.encode("utf-8"))


def test_diagnostics_pass_through_unchanged() -> None:
    from wikiepwing.model.diagnostics import Diagnostic

    diagnostic = Diagnostic(
        code="X",
        severity="info",
        stage="test",
        page_id=1,
        title="Emacs",
        message="msg",
        source_path=None,
        source_excerpt=None,
        details={},
    )
    article = _make_article(diagnostics=(diagnostic,))

    entry = render_article_to_entry(article)

    assert entry.diagnostics == (diagnostic,)


def test_internal_targets_extracted_from_resolved_links() -> None:
    article = _make_article(
        blocks=(
            ParagraphBlock(
                inlines=(
                    InternalLinkInline(
                        label=(TextInline(value="GNU"),),
                        target_title="GNU Project",
                        target_normalized_title="GNU Project",
                        target_fragment=None,
                        target_page_id=42,
                        resolution="resolved",
                    ),
                )
            ),
        )
    )

    entry = render_article_to_entry(article)

    assert entry.internal_targets == (compute_entry_id(42),)


def test_internal_targets_exclude_missing_links() -> None:
    article = _make_article(
        blocks=(
            ParagraphBlock(
                inlines=(
                    InternalLinkInline(
                        label=(TextInline(value="Ghost"),),
                        target_title="Ghost",
                        target_normalized_title="Ghost",
                        target_fragment=None,
                        target_page_id=None,
                        resolution="missing",
                    ),
                )
            ),
        )
    )

    entry = render_article_to_entry(article)

    assert entry.internal_targets == ()


def _cell(text: str, *, is_header: bool = False) -> TableCell:
    return TableCell(
        blocks=(ParagraphBlock(inlines=(TextInline(value=text),)),),
        row_span=1,
        col_span=1,
        is_header=is_header,
    )


def test_simple_table_renders_as_grid_like_text() -> None:
    table = TableBlock(
        caption=(TextInline(value="Sizes"),),
        rows=(
            (_cell("Name", is_header=True), _cell("Size", is_header=True)),
            (_cell("Small"), _cell("1")),
        ),
        source_class_names=(),
        complexity="simple",
    )
    article = _make_article(blocks=(table,))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "Sizes" in text
    assert "Name | Size" in text
    assert "Small | 1" in text


def test_wide_table_with_header_row_renders_labeled_vertical_records() -> None:
    table = TableBlock(
        caption=(TextInline(value="Wide data"),),
        rows=(
            (_cell("Name", is_header=True), _cell("Size", is_header=True)),
            (_cell("Small"), _cell("1")),
            (_cell("Large"), _cell("2")),
        ),
        source_class_names=(),
        complexity="wide",
    )
    article = _make_article(blocks=(table,))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "Wide data" in text
    assert "Name: Small" in text
    assert "Size: 1" in text
    assert "Name: Large" in text
    assert "Size: 2" in text


def test_wide_table_without_header_row_falls_back_to_generic_labels() -> None:
    table = TableBlock(
        caption=(),
        rows=((_cell("a"), _cell("b")),),
        source_class_names=(),
        complexity="wide",
    )
    article = _make_article(blocks=(table,))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "列1: a" in text
    assert "列2: b" in text


def test_complex_table_also_renders_as_vertical_records() -> None:
    table = TableBlock(
        caption=(),
        rows=((_cell("Header", is_header=True),), (_cell("Value"),)),
        source_class_names=(),
        complexity="complex",
    )
    article = _make_article(blocks=(table,))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "Header: Value" in text


def test_unsupported_empty_table_renders_only_its_caption() -> None:
    table = TableBlock(
        caption=(TextInline(value="Empty"),),
        rows=(),
        source_class_names=(),
        complexity="unsupported",
    )
    article = _make_article(blocks=(table,))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "Empty" in text


def test_infobox_renders_title_fields_and_image_placeholder() -> None:
    infobox = InfoboxBlock(
        title="Emacs",
        fields=(
            InfoboxField(
                name="Developer",
                value=(ParagraphBlock(inlines=(TextInline(value="GNU Project"),)),),
            ),
        ),
        images=("emacs.png",),
    )
    article = _make_article(blocks=(infobox,))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "Emacs" in text
    assert "Developer: GNU Project" in text
    assert "[画像: emacs.png]" in text


def test_infobox_without_title_still_renders_fields() -> None:
    infobox = InfoboxBlock(
        title=None,
        fields=(
            InfoboxField(
                name="License", value=(ParagraphBlock(inlines=(TextInline(value="GPL"),)),)
            ),
        ),
        images=(),
    )
    article = _make_article(blocks=(infobox,))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "License: GPL" in text


def test_references_render_as_numbered_list() -> None:
    references = ReferencesBlock(
        items=(
            (TextInline(value="First citation."),),
            (TextInline(value="Second citation."),),
        )
    )
    article = _make_article(blocks=(references,))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "[1] First citation." in text
    assert "[2] Second citation." in text


def test_empty_references_block_renders_no_items() -> None:
    article = _make_article(blocks=(ReferencesBlock(items=()),))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "[1]" not in text


def test_math_block_renders_its_source_as_a_line() -> None:
    from wikiepwing.model.blocks import MathBlock

    article = _make_article(blocks=(MathBlock(source="E=mc^2", source_format="tex"),))

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "E=mc^2" in text


def test_math_inline_renders_its_source_within_the_paragraph_text() -> None:
    from wikiepwing.model.inline import MathInline

    article = _make_article(
        blocks=(
            ParagraphBlock(
                inlines=(
                    TextInline(value="see "),
                    MathInline(source="x^2", source_format="tex"),
                    TextInline(value=" here"),
                ),
            ),
        )
    )

    entry = render_article_to_entry(article)
    text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))

    assert "see x^2 here" in text
