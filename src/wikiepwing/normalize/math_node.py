"""Math node extraction (TASK-N001, ARCHITECTURE.md 15.7).

15.7's math handling priority starts with "1. テキスト代替を保存" and
"2. TeX sourceがあればcache keyに使用". This module extracts both from a
`<math>` (MathML) element using MathML's own standard attributes rather
than MediaWiki-specific wrapper markup this project cannot verify without
a live HTML sample: the `alttext` attribute (the TeX-like text alternative
MediaWiki's Math extension always sets) and the `display` attribute
(`"block"` or `"inline"`, part of the MathML spec itself). The original
TeX source, when present, lives in a nested
`<annotation encoding="application/x-tex">` element -- also a standard
MathML convention for embedding the source that generated a formula, used
by MediaWiki's Math extension.
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode

_TEX_ENCODING = "application/x-tex"


@dataclass(frozen=True, slots=True)
class RawMathNode:
    """One `<math>` element's extracted text alternative, TeX source, and layout."""

    tex_source: str | None
    text_alternative: str | None
    is_block: bool


def is_math_node(node: Node) -> bool:
    """Return whether `node` is a `<math>` (MathML) element."""
    return isinstance(node, ElementNode) and node.tag == "math"


def parse_math_node(node: ElementNode) -> RawMathNode:
    """Extract TeX source, text alternative, and block/inline layout from a `<math>` element."""
    if node.tag != "math":
        raise ValueError(f"not a math element: <{node.tag}>")
    return RawMathNode(
        tex_source=_find_tex_annotation(node),
        text_alternative=_attribute(node, "alttext"),
        is_block=_attribute(node, "display") == "block",
    )


def _find_tex_annotation(node: ElementNode) -> str | None:
    for child in node.children:
        if not isinstance(child, ElementNode):
            continue
        if child.tag == "annotation" and _attribute(child, "encoding") == _TEX_ENCODING:
            text = _flatten_text(child)
            return text if text else None
        found = _find_tex_annotation(child)
        if found is not None:
            return found
    return None


def _attribute(node: ElementNode, name: str) -> str | None:
    for attribute_name, value in node.attributes:
        if attribute_name == name:
            return value
    return None


def _flatten_text(node: ElementNode) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, TextNode):
            parts.append(child.text)
        elif isinstance(child, ElementNode):
            parts.append(_flatten_text(child))
    return "".join(parts).strip()
