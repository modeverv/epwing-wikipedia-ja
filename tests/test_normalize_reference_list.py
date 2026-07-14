from __future__ import annotations

import pytest

from wikiepwing.normalize.html_parser import ElementNode, TextNode, parse_html
from wikiepwing.normalize.reference_list import is_reference_list, parse_reference_list


def _parse(html: str, tag: str) -> ElementNode:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=20)
    return _find(result.root, tag)


def _find(node: ElementNode, tag: str) -> ElementNode:
    found = _find_or_none(node, tag)
    if found is None:
        raise AssertionError(f"<{tag}> not found")
    return found


def _find_or_none(node: ElementNode, tag: str) -> ElementNode | None:
    if node.tag == tag:
        return node
    for child in node.children:
        if isinstance(child, ElementNode):
            found = _find_or_none(child, tag)
            if found is not None:
                return found
    return None


def _text(nodes: tuple[object, ...]) -> str:
    return "".join(node.text for node in nodes if isinstance(node, TextNode))


def test_recognizes_a_reference_list() -> None:
    node = _parse('<ol class="references"><li>x</li></ol>', "ol")

    assert is_reference_list(node) is True


def test_does_not_recognize_a_plain_ol() -> None:
    node = _parse("<ol><li>x</li></ol>", "ol")

    assert is_reference_list(node) is False


def test_parses_note_id_and_reference_text_span() -> None:
    node = _parse(
        '<ol class="references">'
        '<li id="cite_note-1">'
        '<span class="mw-cite-backlink">↑</span>'
        '<span class="reference-text">Citation one.</span>'
        "</li>"
        "</ol>",
        "ol",
    )

    items = parse_reference_list(node)

    assert len(items) == 1
    assert items[0].note_id == "cite_note-1"
    assert _text(items[0].content) == "Citation one."


def test_multiple_items_are_parsed_in_order() -> None:
    node = _parse(
        '<ol class="references">'
        '<li id="cite_note-1"><span class="reference-text">First.</span></li>'
        '<li id="cite_note-2"><span class="reference-text">Second.</span></li>'
        "</ol>",
        "ol",
    )

    items = parse_reference_list(node)

    assert [item.note_id for item in items] == ["cite_note-1", "cite_note-2"]
    assert [_text(item.content) for item in items] == ["First.", "Second."]


def test_falls_back_to_stripping_backlink_when_no_reference_text_span() -> None:
    node = _parse(
        '<ol class="references">'
        '<li id="cite_note-1">'
        '<span class="mw-cite-backlink">↑</span>'
        "Bare citation text."
        "</li>"
        "</ol>",
        "ol",
    )

    items = parse_reference_list(node)

    assert _text(items[0].content) == "Bare citation text."


def test_missing_id_yields_none_note_id() -> None:
    node = _parse(
        '<ol class="references"><li><span class="reference-text">x</span></li></ol>', "ol"
    )

    items = parse_reference_list(node)

    assert items[0].note_id is None


def test_parse_rejects_non_reference_list_element() -> None:
    node = _parse("<ol><li>x</li></ol>", "ol")

    with pytest.raises(ValueError, match="not a reference list"):
        parse_reference_list(node)


def test_non_li_children_are_ignored() -> None:
    node = _parse('<ol class="references">text<li id="cite_note-1">x</li></ol>', "ol")

    items = parse_reference_list(node)

    assert len(items) == 1
