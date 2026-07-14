from __future__ import annotations

from wikiepwing.model.inline import TextInline
from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.references_block import build_references_block


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


def test_builds_references_block_with_converted_inlines() -> None:
    node = _parse(
        '<ol class="references">'
        '<li id="cite_note-1"><span class="reference-text">Citation one.</span></li>'
        '<li id="cite_note-2"><span class="reference-text">Citation two.</span></li>'
        "</ol>",
        "ol",
    )

    block, diagnostics = build_references_block(node)

    assert diagnostics == ()
    assert block.items == (
        (TextInline(value="Citation one."),),
        (TextInline(value="Citation two."),),
    )


def test_empty_reference_list_yields_empty_items() -> None:
    node = _parse('<ol class="references"></ol>', "ol")

    block, _ = build_references_block(node)

    assert block.items == ()


def test_inline_markup_within_a_citation_is_converted() -> None:
    node = _parse(
        '<ol class="references">'
        '<li id="cite_note-1"><span class="reference-text"><b>Bold</b> text.</span></li>'
        "</ol>",
        "ol",
    )

    block, _ = build_references_block(node)

    from wikiepwing.model.inline import StrongInline

    assert block.items[0] == (
        StrongInline(inlines=(TextInline(value="Bold"),)),
        TextInline(value=" text."),
    )
