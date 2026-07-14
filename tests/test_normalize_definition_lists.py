from __future__ import annotations

import pytest

from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.inline import TextInline
from wikiepwing.normalize.definition_lists import convert_definition_list, is_definition_list
from wikiepwing.normalize.html_parser import ElementNode, parse_html


def _first_body_child(html: str) -> ElementNode:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=32)
    html_node = result.root.children[0]
    assert isinstance(html_node, ElementNode)
    body = html_node.children[0]
    assert isinstance(body, ElementNode)
    child = body.children[0]
    assert isinstance(child, ElementNode)
    return child


def test_is_definition_list_matches_dl() -> None:
    dl = _first_body_child("<dl><dt>a</dt><dd>b</dd></dl>")
    assert is_definition_list(dl)


def test_is_definition_list_rejects_other_elements() -> None:
    ul = _first_body_child("<ul><li>a</li></ul>")
    assert not is_definition_list(ul)


def test_convert_definition_list_single_entry() -> None:
    dl = _first_body_child("<dl><dt>Term</dt><dd>Definition</dd></dl>")

    block, diagnostics = convert_definition_list(dl)

    assert diagnostics == ()
    assert len(block.entries) == 1
    entry = block.entries[0]
    assert entry.terms == ((TextInline(value="Term"),),)
    assert entry.definitions == ((ParagraphBlock(inlines=(TextInline(value="Definition"),)),),)


def test_convert_definition_list_groups_multiple_terms() -> None:
    dl = _first_body_child("<dl><dt>Term1</dt><dt>Term2</dt><dd>Def</dd></dl>")

    block, _ = convert_definition_list(dl)

    assert len(block.entries) == 1
    entry = block.entries[0]
    assert entry.terms == ((TextInline(value="Term1"),), (TextInline(value="Term2"),))
    assert len(entry.definitions) == 1


def test_convert_definition_list_groups_multiple_definitions() -> None:
    dl = _first_body_child("<dl><dt>Term</dt><dd>Def1</dd><dd>Def2</dd></dl>")

    block, _ = convert_definition_list(dl)

    assert len(block.entries) == 1
    entry = block.entries[0]
    assert entry.definitions == (
        (ParagraphBlock(inlines=(TextInline(value="Def1"),)),),
        (ParagraphBlock(inlines=(TextInline(value="Def2"),)),),
    )


def test_convert_definition_list_starts_new_entry_after_dt_following_dd() -> None:
    dl = _first_body_child("<dl><dt>Term1</dt><dd>Def1</dd><dt>Term2</dt><dd>Def2</dd></dl>")

    block, _ = convert_definition_list(dl)

    assert len(block.entries) == 2
    assert block.entries[0].terms == ((TextInline(value="Term1"),),)
    assert block.entries[1].terms == ((TextInline(value="Term2"),),)


def test_convert_definition_list_rejects_non_dl_element() -> None:
    ul = _first_body_child("<ul><li>a</li></ul>")

    with pytest.raises(ValueError, match="not a definition list element"):
        convert_definition_list(ul)


def test_convert_definition_list_handles_empty_dl() -> None:
    dl = _first_body_child("<dl></dl>")

    block, diagnostics = convert_definition_list(dl)

    assert block.entries == ()
    assert diagnostics == ()
