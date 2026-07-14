"""Table DOM parser (TASK-K001, ARCHITECTURE.md 11.5).

Parses a raw `<table>` element from TASK-G001's DOM tree into an
intermediate representation (`RawTable`/`RawTableRow`/`RawTableCell`) that
preserves each cell's raw child nodes plus its `rowspan`/`colspan`/header
flag. This is deliberately *not* the final `TableBlock` (ARCHITECTURE.md
11.5): row/col span normalization (TASK-K002), complexity classification
(TASK-K003), and conversion to `TableBlock`/`TableCell` (TASK-K004-K006)
are later tasks that build on this raw structure.
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.html_parser import ElementNode, Node

_CELL_TAGS = frozenset({"td", "th"})
_ROW_CONTAINER_TAGS = frozenset({"thead", "tbody", "tfoot"})


@dataclass(frozen=True, slots=True)
class RawTableCell:
    """One `<td>`/`<th>` cell, unexpanded."""

    content: tuple[Node, ...]
    row_span: int
    col_span: int
    is_header: bool


@dataclass(frozen=True, slots=True)
class RawTableRow:
    """One `<tr>` row's cells, in DOM order."""

    cells: tuple[RawTableCell, ...]


@dataclass(frozen=True, slots=True)
class RawTable:
    """A `<table>` element parsed into rows/cells, before span normalization."""

    caption: tuple[Node, ...]
    rows: tuple[RawTableRow, ...]
    source_class_names: tuple[str, ...]


def is_table(node: Node) -> bool:
    """Return whether `node` is a `<table>` element."""
    return isinstance(node, ElementNode) and node.tag == "table"


def parse_table_dom(node: ElementNode) -> tuple[RawTable, tuple[Diagnostic, ...]]:
    """Parse one `<table>` element into a RawTable, plus any diagnostics."""
    if node.tag != "table":
        raise ValueError(f"not a table element: <{node.tag}>")

    diagnostics: list[Diagnostic] = []
    caption = _find_caption(node)
    rows = []
    for tr in _find_rows(node):
        cells, cell_diagnostics = _parse_row(tr)
        rows.append(RawTableRow(cells=cells))
        diagnostics.extend(cell_diagnostics)

    table = RawTable(
        caption=caption,
        rows=tuple(rows),
        source_class_names=_class_names(node),
    )
    return table, tuple(diagnostics)


def _class_names(node: ElementNode) -> tuple[str, ...]:
    for name, value in node.attributes:
        if name == "class":
            return tuple(value.split())
    return ()


def _find_caption(table: ElementNode) -> tuple[Node, ...]:
    for child in table.children:
        if isinstance(child, ElementNode) and child.tag == "caption":
            return child.children
    return ()


def _find_rows(table: ElementNode) -> list[ElementNode]:
    """Return this table's own `<tr>` rows, never descending into a nested table."""
    rows: list[ElementNode] = []
    for child in table.children:
        if not isinstance(child, ElementNode):
            continue
        if child.tag == "tr":
            rows.append(child)
        elif child.tag in _ROW_CONTAINER_TAGS:
            rows.extend(_find_rows_in_container(child))
    return rows


def _find_rows_in_container(container: ElementNode) -> list[ElementNode]:
    return [
        child
        for child in container.children
        if isinstance(child, ElementNode) and child.tag == "tr"
    ]


def _parse_row(tr: ElementNode) -> tuple[tuple[RawTableCell, ...], list[Diagnostic]]:
    cells: list[RawTableCell] = []
    diagnostics: list[Diagnostic] = []
    for child in tr.children:
        if not isinstance(child, ElementNode) or child.tag not in _CELL_TAGS:
            continue
        row_span, row_span_diagnostic = _parse_span(child, "rowspan")
        col_span, col_span_diagnostic = _parse_span(child, "colspan")
        if row_span_diagnostic is not None:
            diagnostics.append(row_span_diagnostic)
        if col_span_diagnostic is not None:
            diagnostics.append(col_span_diagnostic)
        cells.append(
            RawTableCell(
                content=child.children,
                row_span=row_span,
                col_span=col_span,
                is_header=child.tag == "th",
            )
        )
    return tuple(cells), diagnostics


def _parse_span(cell: ElementNode, attribute: str) -> tuple[int, Diagnostic | None]:
    raw_value = _attribute(cell, attribute)
    if raw_value is None:
        return 1, None
    try:
        value = int(raw_value)
    except ValueError:
        return 1, _invalid_span_diagnostic(cell, attribute, raw_value)
    if value < 1:
        return 1, _invalid_span_diagnostic(cell, attribute, raw_value)
    return value, None


def _attribute(node: ElementNode, name: str) -> str | None:
    for attribute_name, value in node.attributes:
        if attribute_name == name:
            return value
    return None


def _invalid_span_diagnostic(cell: ElementNode, attribute: str, raw_value: str) -> Diagnostic:
    return Diagnostic(
        code="TABLE_INVALID_SPAN",
        severity="warning",
        stage="normalize_tables",
        page_id=None,
        title=None,
        message=f"<{cell.tag} {attribute}={raw_value!r}> is not a valid span; using 1",
        source_path=None,
        source_excerpt=None,
        details={"attribute": attribute, "raw_value": raw_value},
    )
