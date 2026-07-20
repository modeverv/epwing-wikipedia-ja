from __future__ import annotations

from wikiepwing.render.render_node import (
    GraphicRenderNode,
    LineBreakRenderNode,
    LinkRenderNode,
    TextRenderNode,
)


def test_text_render_node_holds_text() -> None:
    node = TextRenderNode(text="hello")

    assert node.text == "hello"


def test_line_break_render_node_has_no_fields() -> None:
    node = LineBreakRenderNode()

    assert node == LineBreakRenderNode()


def test_link_render_node_holds_label_and_target() -> None:
    node = LinkRenderNode(label="GNU Project", target="p42")

    assert node.label == "GNU Project"
    assert node.target == "p42"


def test_graphic_render_node_holds_catalog_name() -> None:
    assert GraphicRenderNode(name="abc123").name == "abc123"
