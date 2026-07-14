from __future__ import annotations

import pytest

from wikiepwing.model.blocks import HeadingBlock, ParagraphBlock, UnsupportedBlock
from wikiepwing.model.inline import TextInline
from wikiepwing.normalize.html_parser import HtmlParseError
from wikiepwing.normalize.pipeline import NormalizeOptions, normalize_html

_DEFAULT_OPTIONS = NormalizeOptions(
    max_dom_depth=64,
    html_recover=True,
    remove_edit_ui=True,
    remove_navboxes=True,
    remove_authority_control=True,
)


def test_normalize_html_produces_paragraph_and_heading() -> None:
    html = "<html><body><h2>Title</h2><p>Body text</p></body></html>"

    blocks, diagnostics = normalize_html(html, _DEFAULT_OPTIONS)

    assert isinstance(blocks[0], HeadingBlock)
    assert blocks[1] == ParagraphBlock(inlines=(TextInline(value="Body text"),))
    assert diagnostics == ()


def test_normalize_html_selects_mw_parser_output_and_strips_edit_ui() -> None:
    html = (
        "<html><body>"
        '<div class="mw-parser-output">'
        '<p>keep<span class="mw-editsection">[edit]</span></p>'
        "</div></body></html>"
    )

    blocks, diagnostics = normalize_html(html, _DEFAULT_OPTIONS)

    assert blocks == (ParagraphBlock(inlines=(TextInline(value="keep"),)),)
    codes = {d.code for d in diagnostics}
    assert "DOM_EDIT_UI_REMOVED" in codes


def test_normalize_html_collapses_whitespace() -> None:
    html = "<html><body><p>a   b\n\n c</p></body></html>"

    blocks, _ = normalize_html(html, _DEFAULT_OPTIONS)

    assert blocks == (ParagraphBlock(inlines=(TextInline(value="a b c"),)),)


def test_normalize_html_falls_back_for_unknown_block_elements() -> None:
    html = "<html><body><figure>cell</figure></body></html>"

    blocks, diagnostics = normalize_html(html, _DEFAULT_OPTIONS)

    assert isinstance(blocks[0], UnsupportedBlock)
    codes = {d.code for d in diagnostics}
    assert "DOM_UNKNOWN_ELEMENT" in codes


def test_normalize_html_disables_recovery_raises_on_malformed_html() -> None:
    options = NormalizeOptions(
        max_dom_depth=64,
        html_recover=False,
        remove_edit_ui=True,
        remove_navboxes=True,
        remove_authority_control=True,
    )

    with pytest.raises(HtmlParseError):
        normalize_html("<p>text</div></p>", options)


def test_normalize_html_empty_document_produces_no_blocks() -> None:
    blocks, diagnostics = normalize_html("", _DEFAULT_OPTIONS)

    assert blocks == ()
    assert diagnostics == ()
