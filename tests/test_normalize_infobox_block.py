from __future__ import annotations

from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.inline import TextInline
from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.infobox_block import build_infobox_block


def _parse_table(html: str) -> ElementNode:
    result = parse_html(html, max_dom_depth=50)
    return _find(result.root, "table")


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


def test_builds_infobox_with_title_and_fields() -> None:
    table = _parse_table(
        "<table>"
        '<tr><th colspan="2">Emacs</th></tr>'
        "<tr><th>Developer</th><td>GNU Project</td></tr>"
        "</table>"
    )

    block, diagnostics = build_infobox_block(table)

    assert diagnostics == ()
    assert block.title == "Emacs"
    assert len(block.fields) == 1
    assert block.fields[0].name == "Developer"


def test_field_value_is_converted_to_blocks() -> None:
    table = _parse_table("<table><tr><th>Developer</th><td><p>GNU Project</p></td></tr></table>")

    block, _ = build_infobox_block(table)

    value_blocks = block.fields[0].value
    assert len(value_blocks) == 1
    paragraph = value_blocks[0]
    assert isinstance(paragraph, ParagraphBlock)
    assert paragraph.inlines == (TextInline(value="GNU Project"),)


def test_images_are_carried_through() -> None:
    table = _parse_table('<table><tr><td colspan="2"><img src="emacs.png"></td></tr></table>')

    block, _ = build_infobox_block(table)

    assert block.images == ("emacs.png",)


def test_empty_infobox_records_a_diagnostic() -> None:
    table = _parse_table("<table></table>")

    block, diagnostics = build_infobox_block(table)

    assert block.title is None
    assert block.fields == ()
    assert block.images == ()
    assert any(diagnostic.code == "INFOBOX_EMPTY" for diagnostic in diagnostics)


def test_non_empty_infobox_does_not_record_empty_diagnostic() -> None:
    table = _parse_table('<table><tr><th colspan="2">Emacs</th></tr></table>')

    _, diagnostics = build_infobox_block(table)

    assert not any(diagnostic.code == "INFOBOX_EMPTY" for diagnostic in diagnostics)


def test_diagnostics_from_row_parsing_are_propagated() -> None:
    table = _parse_table('<table><tr><td colspan="bogus">x</td></tr></table>')

    _, diagnostics = build_infobox_block(table)

    assert any(diagnostic.code == "TABLE_INVALID_SPAN" for diagnostic in diagnostics)


def test_field_name_that_normalizes_empty_is_skipped_with_diagnostic() -> None:
    table = _parse_table("<table><tr><th>\u200b</th><td>value</td></tr></table>")

    block, diagnostics = build_infobox_block(table)

    assert block.fields == ()
    assert any(diagnostic.code == "INFOBOX_EMPTY_FIELD_NAME" for diagnostic in diagnostics)
