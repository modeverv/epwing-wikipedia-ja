from __future__ import annotations

from wikiepwing.normalize.html_parser import ElementNode, TextNode, parse_html
from wikiepwing.normalize.infobox_fields import parse_infobox_dom


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


def _text(nodes: tuple[object, ...]) -> str:
    return "".join(node.text for node in nodes if isinstance(node, TextNode))


def test_title_row_is_extracted() -> None:
    table = _parse_table('<table><tr><th colspan="2">Emacs</th></tr></table>')

    infobox, _ = parse_infobox_dom(table)

    assert infobox.title == "Emacs"


def test_two_cell_rows_become_fields() -> None:
    table = _parse_table(
        "<table>"
        '<tr><th colspan="2">Emacs</th></tr>'
        "<tr><th>Developer</th><td>GNU Project</td></tr>"
        "<tr><th>License</th><td>GPL</td></tr>"
        "</table>"
    )

    infobox, _ = parse_infobox_dom(table)

    assert [field.name for field in infobox.fields] == ["Developer", "License"]
    assert _text(infobox.fields[0].value_nodes) == "GNU Project"
    assert _text(infobox.fields[1].value_nodes) == "GPL"


def test_image_row_src_is_extracted() -> None:
    table = _parse_table(
        '<table><tr><td colspan="2"><img src="emacs.png" alt="logo"></td></tr></table>'
    )

    infobox, _ = parse_infobox_dom(table)

    assert infobox.image_srcs == ("emacs.png",)


def test_image_inside_a_field_value_is_also_extracted() -> None:
    table = _parse_table('<table><tr><th>Logo</th><td><img src="emacs.png"></td></tr></table>')

    infobox, _ = parse_infobox_dom(table)

    assert infobox.image_srcs == ("emacs.png",)
    assert infobox.fields[0].name == "Logo"


def test_table_without_title_row_has_none_title() -> None:
    table = _parse_table("<table><tr><th>Developer</th><td>GNU</td></tr></table>")

    infobox, _ = parse_infobox_dom(table)

    assert infobox.title is None


def test_unrecognized_row_shapes_are_skipped() -> None:
    table = _parse_table(
        "<table>"
        '<tr><th colspan="2">Emacs</th></tr>'
        '<tr><td colspan="2">unstructured note</td></tr>'
        "<tr><th>Developer</th><td>GNU</td></tr>"
        "</table>"
    )

    infobox, _ = parse_infobox_dom(table)

    assert infobox.title == "Emacs"
    assert [field.name for field in infobox.fields] == ["Developer"]


def test_diagnostics_from_table_parsing_are_propagated() -> None:
    table = _parse_table('<table><tr><td colspan="bogus">x</td></tr></table>')

    _, diagnostics = parse_infobox_dom(table)

    assert any(diagnostic.code == "TABLE_INVALID_SPAN" for diagnostic in diagnostics)
