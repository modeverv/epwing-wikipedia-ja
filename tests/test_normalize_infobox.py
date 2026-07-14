from __future__ import annotations

from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.infobox import is_infobox


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


def _parse(html: str, tag: str) -> ElementNode:
    result = parse_html(html, max_dom_depth=50)
    return _find(result.root, tag)


def test_table_with_infobox_class_is_detected() -> None:
    table = _parse('<table class="infobox"><tr><td>x</td></tr></table>', "table")

    assert is_infobox(table) is True


def test_table_with_infobox_among_multiple_classes_is_detected() -> None:
    table = _parse('<table class="infobox biography vcard"><tr><td>x</td></tr></table>', "table")

    assert is_infobox(table) is True


def test_table_without_infobox_class_is_not_detected() -> None:
    table = _parse('<table class="wikitable"><tr><td>x</td></tr></table>', "table")

    assert is_infobox(table) is False


def test_table_without_class_attribute_is_not_detected() -> None:
    table = _parse("<table><tr><td>x</td></tr></table>", "table")

    assert is_infobox(table) is False


def test_non_table_element_is_not_detected() -> None:
    div = _parse('<div class="infobox">x</div>', "div")

    assert is_infobox(div) is False


def test_class_prefix_alone_does_not_match() -> None:
    # "infoboxen" should not match on a naive substring check.
    table = _parse('<table class="infoboxen"><tr><td>x</td></tr></table>', "table")

    assert is_infobox(table) is False
