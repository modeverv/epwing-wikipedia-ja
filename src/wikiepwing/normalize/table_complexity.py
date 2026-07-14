"""Table complexity classifier (TASK-K003, ARCHITECTURE.md 11.5/16.3).

`ARCHITECTURE.md` 16.3 states the render policy for each `TableComplexity`
tier ("simple": narrow columns / short cells / grid-like text; "wide":
show each row as a vertical record; "complex": treat each row/section as
key-value pairs) but does not specify concrete thresholds. This module
documents the concrete judgment call this project makes, since none is
given elsewhere:

- `unsupported`: the table has no rows at all -- nothing meaningful to
  grid-render, key-value-ize, or record-ize.
- `complex`: at least one cell has a rowspan or colspan greater than 1.
  Any merged cell breaks the simple row-is-a-record/column-is-a-field
  assumption 16.3's "simple"/"wide" tiers rely on, so it needs the
  row/section key-value treatment "complex" describes -- regardless of
  column count.
- `wide`: no merged cells, but the column count exceeds
  `max_simple_columns` (default 6, chosen so a Mini-profile plain-text
  grid render stays legible without needing real column-width layout).
- `simple`: no merged cells and the column count is within that limit.
"""

from __future__ import annotations

from wikiepwing.model.blocks import TableComplexity
from wikiepwing.normalize.table_grid import NormalizedTable

DEFAULT_MAX_SIMPLE_COLUMNS = 6


def classify_table_complexity(
    table: NormalizedTable, *, max_simple_columns: int = DEFAULT_MAX_SIMPLE_COLUMNS
) -> TableComplexity:
    """Classify a NormalizedTable per the tiers documented above."""
    if not table.rows:
        return "unsupported"
    if _has_merged_cell(table):
        return "complex"
    if table.column_count > max_simple_columns:
        return "wide"
    return "simple"


def _has_merged_cell(table: NormalizedTable) -> bool:
    return any(
        positioned.cell.row_span > 1 or positioned.cell.col_span > 1
        for row in table.rows
        for positioned in row
    )
