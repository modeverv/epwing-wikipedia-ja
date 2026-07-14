from __future__ import annotations

from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.unsafe_nodes import UnsafeNodeRemovalOptions, remove_unsafe_nodes

_ALL_ENABLED = UnsafeNodeRemovalOptions(
    remove_edit_ui=True, remove_navboxes=True, remove_authority_control=True
)
_ALL_DISABLED = UnsafeNodeRemovalOptions(
    remove_edit_ui=False, remove_navboxes=False, remove_authority_control=False
)


def _parse_body_children(html: str) -> tuple[ElementNode, ...]:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=32)
    html_node = result.root.children[0]
    assert isinstance(html_node, ElementNode)
    body = html_node.children[0]
    assert isinstance(body, ElementNode)
    return tuple(child for child in body.children if isinstance(child, ElementNode))


def test_script_and_style_are_always_removed() -> None:
    children = _parse_body_children(
        "<p>keep</p><script>alert(1)</script><style>p{color:red}</style>"
    )

    kept, diagnostics = remove_unsafe_nodes(children, _ALL_DISABLED)

    assert [node.tag for node in kept if isinstance(node, ElementNode)] == ["p"]
    codes = {d.code for d in diagnostics}
    assert codes == {"DOM_EXECUTABLE_CONTENT_REMOVED"}
    assert len(diagnostics) == 2


def test_removes_edit_ui_when_enabled() -> None:
    children = _parse_body_children('<p>text<span class="mw-editsection">[edit]</span></p>')

    kept, diagnostics = remove_unsafe_nodes(children, _ALL_ENABLED)

    p = kept[0]
    assert isinstance(p, ElementNode)
    assert not any(isinstance(child, ElementNode) and child.tag == "span" for child in p.children)
    codes = {d.code for d in diagnostics}
    assert "DOM_EDIT_UI_REMOVED" in codes


def test_keeps_edit_ui_when_disabled() -> None:
    children = _parse_body_children('<p><span class="mw-editsection">[edit]</span></p>')

    kept, diagnostics = remove_unsafe_nodes(children, _ALL_DISABLED)

    p = kept[0]
    assert isinstance(p, ElementNode)
    assert any(isinstance(child, ElementNode) and child.tag == "span" for child in p.children)
    assert diagnostics == ()


def test_removes_navbox_when_enabled() -> None:
    children = _parse_body_children('<div class="navbox">nav</div><p>keep</p>')

    kept, diagnostics = remove_unsafe_nodes(children, _ALL_ENABLED)

    tags = [node.tag for node in kept if isinstance(node, ElementNode)]
    assert tags == ["p"]
    codes = {d.code for d in diagnostics}
    assert "DOM_NAVBOX_REMOVED" in codes


def test_keeps_navbox_when_disabled() -> None:
    children = _parse_body_children('<div class="navbox">nav</div><p>keep</p>')

    kept, diagnostics = remove_unsafe_nodes(children, _ALL_DISABLED)

    tags = [node.tag for node in kept if isinstance(node, ElementNode)]
    assert tags == ["div", "p"]
    assert diagnostics == ()


def test_removes_authority_control_when_enabled() -> None:
    children = _parse_body_children('<div class="authority-control">links</div><p>keep</p>')

    kept, diagnostics = remove_unsafe_nodes(children, _ALL_ENABLED)

    tags = [node.tag for node in kept if isinstance(node, ElementNode)]
    assert tags == ["p"]
    codes = {d.code for d in diagnostics}
    assert "DOM_AUTHORITY_CONTROL_REMOVED" in codes


def test_removal_is_recursive_and_preserves_unrelated_siblings() -> None:
    children = _parse_body_children(
        '<div><p>before</p><div class="navbox">nav</div><p>after</p></div>'
    )

    kept, diagnostics = remove_unsafe_nodes(children, _ALL_ENABLED)

    outer = kept[0]
    assert isinstance(outer, ElementNode)
    inner_tags = [child.tag for child in outer.children if isinstance(child, ElementNode)]
    assert inner_tags == ["p", "p"]
    codes = {d.code for d in diagnostics}
    assert "DOM_NAVBOX_REMOVED" in codes


def test_no_removal_needed_returns_empty_diagnostics() -> None:
    children = _parse_body_children("<p>plain content</p>")

    kept, diagnostics = remove_unsafe_nodes(children, _ALL_ENABLED)

    assert len(kept) == 1
    assert diagnostics == ()
