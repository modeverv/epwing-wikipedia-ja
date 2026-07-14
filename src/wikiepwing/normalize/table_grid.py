"""Row/col span normalization (TASK-K002, ARCHITECTURE.md 11.5).

`TableCell`/`TableBlock` keep each cell's raw `row_span`/`col_span` rather
than a fully expanded grid, so this task does not change the model. It
computes, from TASK-K001's `RawTable`, each cell's actual grid position
(the HTML "table grid formation algorithm": cells occupied by an ongoing
rowspan from an earlier row push later cells in the same row further
right) and the table's overall column count. Complexity classification
(TASK-K003) and rendering (TASK-K004/K005) need this positional
information; the model itself has no reason to store it.
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.normalize.html_parser import Node
from wikiepwing.normalize.tables import RawTable, RawTableCell


@dataclass(frozen=True, slots=True)
class PositionedCell:
    """One cell plus its resolved starting position in the table's grid."""

    cell: RawTableCell
    row_index: int
    col_index: int


@dataclass(frozen=True, slots=True)
class NormalizedTable:
    """A RawTable with every cell's grid position resolved."""

    caption: tuple[Node, ...]
    rows: tuple[tuple[PositionedCell, ...], ...]
    source_class_names: tuple[str, ...]
    column_count: int


def normalize_table_spans(table: RawTable) -> NormalizedTable:
    """Resolve each cell's grid position, accounting for rowspan/colspan."""
    # active_spans maps an occupied column to how many more rows (including
    # the current one) it remains reserved for, carried forward as each row
    # is processed.
    active_spans: dict[int, int] = {}
    positioned_rows: list[tuple[PositionedCell, ...]] = []
    column_count = 0

    for row_index, row in enumerate(table.rows):
        positioned_cells: list[PositionedCell] = []
        col = 0
        for cell in row.cells:
            while active_spans.get(col, 0) > 0:
                col += 1
            positioned_cells.append(PositionedCell(cell=cell, row_index=row_index, col_index=col))
            if cell.row_span > 1:
                for occupied_col in range(col, col + cell.col_span):
                    active_spans[occupied_col] = cell.row_span
            column_count = max(column_count, col + cell.col_span)
            col += cell.col_span
        positioned_rows.append(tuple(positioned_cells))
        active_spans = {
            occupied_col: remaining - 1
            for occupied_col, remaining in active_spans.items()
            if remaining - 1 > 0
        }

    return NormalizedTable(
        caption=table.caption,
        rows=tuple(positioned_rows),
        source_class_names=table.source_class_names,
        column_count=column_count,
    )
