from __future__ import annotations

from wikiepwing.render.render_node import LineBreakRenderNode, TextRenderNode


def test_text_render_node_holds_text() -> None:
    node = TextRenderNode(text="hello")

    assert node.text == "hello"


def test_line_break_render_node_has_no_fields() -> None:
    node = LineBreakRenderNode()

    assert node == LineBreakRenderNode()
