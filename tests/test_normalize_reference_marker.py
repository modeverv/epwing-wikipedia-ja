from __future__ import annotations

import pytest

from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.reference_marker import (
    is_reference_marker,
    parse_reference_marker,
)


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


def test_recognizes_a_reference_marker() -> None:
    node = _parse(
        '<sup id="cite_ref-1" class="reference"><a href="#cite_note-1">[1]</a></sup>', "sup"
    )

    assert is_reference_marker(node) is True


def test_does_not_recognize_a_plain_sup() -> None:
    node = _parse("<sup>2</sup>", "sup")

    assert is_reference_marker(node) is False


def test_does_not_recognize_a_non_sup_element() -> None:
    node = _parse('<span class="reference">x</span>', "span")

    assert is_reference_marker(node) is False


def test_parses_label_and_target_id() -> None:
    node = _parse(
        '<sup id="cite_ref-1" class="reference"><a href="#cite_note-1">[1]</a></sup>', "sup"
    )

    marker = parse_reference_marker(node)

    assert marker.label == "[1]"
    assert marker.target_id == "cite_note-1"


def test_missing_anchor_yields_no_target_id() -> None:
    node = _parse('<sup class="reference">[1]</sup>', "sup")

    marker = parse_reference_marker(node)

    assert marker.label == "[1]"
    assert marker.target_id is None


def test_non_fragment_href_yields_no_target_id() -> None:
    node = _parse('<sup class="reference"><a href="https://example.com">[1]</a></sup>', "sup")

    marker = parse_reference_marker(node)

    assert marker.target_id is None


def test_parse_rejects_non_marker_element() -> None:
    node = _parse("<sup>2</sup>", "sup")

    with pytest.raises(ValueError, match="not a reference marker"):
        parse_reference_marker(node)
