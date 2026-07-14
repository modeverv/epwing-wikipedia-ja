"""Infobox field parser (TASK-K008, ARCHITECTURE.md 11.6).

Reuses TASK-K001's `parse_table_dom` to read a MediaWiki infobox's rows,
then classifies each row by its common shapes:

- a single header cell (`is_header`, alone in its row) is the infobox's
  title;
- two cells (label, value) form one `RawInfoboxField`;
- a row containing only an `<img>` (or whose lone cell contains one) adds
  that image's `src` to `image_srcs`.

Any row that matches none of these (nested sub-tables, section dividers,
multi-column data some infobox variants use) is silently skipped -- a
documented simplification, not every real-world infobox layout is
supported. Image `src` values are kept as raw strings; turning them into
real `MediaReference`s (downloading, licensing) is a separate epic
(ARCHITECTURE.md 15.1) this task does not touch. Building the actual
`InfoboxBlock`/`InfoboxField` model and rendering it are TASK-K009.
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.html_parser import ElementNode, Node
from wikiepwing.normalize.tables import RawTableCell, parse_table_dom


@dataclass(frozen=True, slots=True)
class RawInfoboxField:
    """One label/value pair extracted from a two-cell infobox row."""

    name: str
    value_nodes: tuple[Node, ...]


@dataclass(frozen=True, slots=True)
class RawInfobox:
    """An infobox parsed into title/fields/image references."""

    title: str | None
    fields: tuple[RawInfoboxField, ...]
    image_srcs: tuple[str, ...]


def parse_infobox_dom(table_element: ElementNode) -> tuple[RawInfobox, tuple[Diagnostic, ...]]:
    """Parse one infobox `<table>` element into a RawInfobox."""
    raw_table, diagnostics = parse_table_dom(table_element)

    title: str | None = None
    fields: list[RawInfoboxField] = []
    image_srcs: list[str] = []

    for row in raw_table.rows:
        cells = row.cells
        if title is None and len(cells) == 1 and cells[0].is_header:
            text = _flatten_text(cells[0].content)
            if text:
                title = text
                continue
        if len(cells) == 1:
            image_srcs.extend(_find_image_srcs(cells[0]))
            continue
        if len(cells) == 2:
            name = _flatten_text(cells[0].content)
            if name:
                fields.append(RawInfoboxField(name=name, value_nodes=cells[1].content))
                image_srcs.extend(_find_image_srcs(cells[1]))
                continue
        # Unrecognized row shape (nested sub-table, section divider,
        # multi-column data): skipped, per this module's documented scope.

    infobox = RawInfobox(title=title, fields=tuple(fields), image_srcs=tuple(image_srcs))
    return infobox, diagnostics


def _find_image_srcs(cell: RawTableCell) -> list[str]:
    return [src for node in cell.content for src in _find_image_srcs_in_node(node)]


def _find_image_srcs_in_node(node: Node) -> list[str]:
    if not isinstance(node, ElementNode):
        return []
    found: list[str] = []
    if node.tag == "img":
        src = _attribute(node, "src")
        if src:
            found.append(src)
    for child in node.children:
        found.extend(_find_image_srcs_in_node(child))
    return found


def _attribute(node: ElementNode, name: str) -> str | None:
    for attribute_name, value in node.attributes:
        if attribute_name == name:
            return value
    return None


def _flatten_text(nodes: tuple[Node, ...]) -> str:
    parts: list[str] = []
    for node in nodes:
        parts.append(_flatten_text_node(node))
    return "".join(parts).strip()


def _flatten_text_node(node: Node) -> str:
    if isinstance(node, ElementNode):
        return "".join(_flatten_text_node(child) for child in node.children)
    return node.text
