"""Build a TableBlock from a `<table>` element (TASK-K004, ARCHITECTURE.md 11.5).

Chains TASK-K001's DOM parse, TASK-K002's span normalization (needed only
to feed TASK-K003's column count), and TASK-K003's complexity
classification, then converts each cell's raw content nodes into `Block`s
(`wikiepwing.normalize.convert_block.convert_document`) and the caption
into `Inline`s (`wikiepwing.normalize.paragraphs.convert_inline_nodes`) to
assemble the actual model `TableBlock`/`TableCell` (ARCHITECTURE.md 11.5).
`TableBlock.rows` mirrors the DOM's own row/cell shape (spans are kept as
metadata, not expanded into a grid) -- TASK-K002's grid positions are only
needed here to compute the column count for TASK-K003's classifier.
"""

from __future__ import annotations

from wikiepwing.model.blocks import TableBlock, TableCell
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.convert_block import convert_document
from wikiepwing.normalize.html_parser import ElementNode
from wikiepwing.normalize.paragraphs import convert_inline_nodes
from wikiepwing.normalize.table_complexity import classify_table_complexity
from wikiepwing.normalize.table_grid import normalize_table_spans
from wikiepwing.normalize.tables import parse_table_dom


def build_table_block(table_element: ElementNode) -> tuple[TableBlock, tuple[Diagnostic, ...]]:
    """Parse, classify, and convert one `<table>` element into a TableBlock."""
    raw_table, parse_diagnostics = parse_table_dom(table_element)
    grid = normalize_table_spans(raw_table)
    complexity = classify_table_complexity(grid)

    diagnostics: list[Diagnostic] = list(parse_diagnostics)
    rows = []
    for raw_row in raw_table.rows:
        cells = []
        for raw_cell in raw_row.cells:
            blocks, cell_diagnostics = convert_document(raw_cell.content)
            diagnostics.extend(cell_diagnostics)
            cells.append(
                TableCell(
                    blocks=blocks,
                    row_span=raw_cell.row_span,
                    col_span=raw_cell.col_span,
                    is_header=raw_cell.is_header,
                )
            )
        rows.append(tuple(cells))

    table = TableBlock(
        caption=convert_inline_nodes(raw_table.caption),
        rows=tuple(rows),
        source_class_names=raw_table.source_class_names,
        complexity=complexity,
    )
    return table, tuple(diagnostics)
