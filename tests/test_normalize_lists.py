from __future__ import annotations

import pytest

from wikiepwing.model.blocks import OrderedListBlock, ParagraphBlock, UnorderedListBlock
from wikiepwing.model.inline import TextInline
from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.lists import (
    convert_ordered_list,
    convert_unordered_list,
    is_ordered_list,
    is_unordered_list,
)


def _first_body_child(html: str) -> ElementNode:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=32)
    html_node = result.root.children[0]
    assert isinstance(html_node, ElementNode)
    body = html_node.children[0]
    assert isinstance(body, ElementNode)
    child = body.children[0]
    assert isinstance(child, ElementNode)
    return child


def test_is_unordered_list_matches_ul() -> None:
    ul = _first_body_child("<ul><li>a</li></ul>")
    assert is_unordered_list(ul)
    assert not is_ordered_list(ul)


def test_is_ordered_list_matches_ol() -> None:
    ol = _first_body_child("<ol><li>a</li></ol>")
    assert is_ordered_list(ol)
    assert not is_unordered_list(ol)


def test_convert_unordered_list_produces_paragraph_per_item() -> None:
    ul = _first_body_child("<ul><li>one</li><li>two</li></ul>")

    block, diagnostics = convert_unordered_list(ul)

    assert isinstance(block, UnorderedListBlock)
    assert diagnostics == ()
    assert len(block.items) == 2
    assert block.items[0].blocks == (ParagraphBlock(inlines=(TextInline(value="one"),)),)
    assert block.items[1].blocks == (ParagraphBlock(inlines=(TextInline(value="two"),)),)


def test_convert_ordered_list_produces_paragraph_per_item() -> None:
    ol = _first_body_child("<ol><li>first</li><li>second</li></ol>")

    block, diagnostics = convert_ordered_list(ol)

    assert isinstance(block, OrderedListBlock)
    assert diagnostics == ()
    assert len(block.items) == 2
    assert block.items[0].blocks == (ParagraphBlock(inlines=(TextInline(value="first"),)),)


def test_convert_unordered_list_rejects_non_ul_element() -> None:
    ol = _first_body_child("<ol><li>a</li></ol>")

    with pytest.raises(ValueError, match="not an unordered list element"):
        convert_unordered_list(ol)


def test_convert_ordered_list_rejects_non_ol_element() -> None:
    ul = _first_body_child("<ul><li>a</li></ul>")

    with pytest.raises(ValueError, match="not an ordered list element"):
        convert_ordered_list(ul)


def test_nested_unordered_list_becomes_separate_block() -> None:
    ul = _first_body_child("<ul><li>outer<ul><li>inner</li></ul></li></ul>")

    block, _ = convert_unordered_list(ul)

    item = block.items[0]
    assert len(item.blocks) == 2
    assert item.blocks[0] == ParagraphBlock(inlines=(TextInline(value="outer"),))
    nested = item.blocks[1]
    assert isinstance(nested, UnorderedListBlock)
    assert nested.items[0].blocks == (ParagraphBlock(inlines=(TextInline(value="inner"),)),)


def test_list_item_with_only_nested_list_has_no_extra_paragraph() -> None:
    ul = _first_body_child("<ul><li><ul><li>inner</li></ul></li></ul>")

    block, _ = convert_unordered_list(ul)

    item = block.items[0]
    assert len(item.blocks) == 1
    assert isinstance(item.blocks[0], UnorderedListBlock)


def test_deeply_nested_lists_report_no_diagnostics() -> None:
    ul = _first_body_child("<ul><li>a<ul><li>b<ol><li>c</li></ol></li></ul></li></ul>")

    _, diagnostics = convert_unordered_list(ul)

    assert diagnostics == ()


def test_non_li_children_are_ignored() -> None:
    ul = _first_body_child("<ul>stray text<li>real</li></ul>")

    block, _ = convert_unordered_list(ul)

    assert len(block.items) == 1
