from __future__ import annotations

from wikiepwing.normalize.table_complexity import classify_table_complexity
from wikiepwing.normalize.table_grid import NormalizedTable as Grid
from wikiepwing.normalize.table_grid import PositionedCell
from wikiepwing.normalize.tables import RawTableCell


def _cell(row_span: int = 1, col_span: int = 1) -> RawTableCell:
    return RawTableCell(content=(), row_span=row_span, col_span=col_span, is_header=False)


def _grid(rows: list[list[RawTableCell]], column_count: int) -> Grid:
    positioned_rows = tuple(
        tuple(
            PositionedCell(cell=cell, row_index=row_index, col_index=col_index)
            for col_index, cell in enumerate(row)
        )
        for row_index, row in enumerate(rows)
    )
    return Grid(caption=(), rows=positioned_rows, source_class_names=(), column_count=column_count)


def test_empty_table_is_unsupported() -> None:
    grid = _grid([], column_count=0)

    assert classify_table_complexity(grid) == "unsupported"


def test_small_table_without_spans_is_simple() -> None:
    grid = _grid([[_cell(), _cell()], [_cell(), _cell()]], column_count=2)

    assert classify_table_complexity(grid) == "simple"


def test_table_at_the_threshold_is_still_simple() -> None:
    row = [_cell() for _ in range(6)]
    grid = _grid([row], column_count=6)

    assert classify_table_complexity(grid) == "simple"


def test_table_beyond_the_threshold_is_wide() -> None:
    row = [_cell() for _ in range(7)]
    grid = _grid([row], column_count=7)

    assert classify_table_complexity(grid) == "wide"


def test_custom_threshold_is_honored() -> None:
    row = [_cell(), _cell(), _cell()]
    grid = _grid([row], column_count=3)

    assert classify_table_complexity(grid, max_simple_columns=2) == "wide"


def test_rowspan_makes_a_table_complex_even_if_narrow() -> None:
    grid = _grid([[_cell(row_span=2)]], column_count=1)

    assert classify_table_complexity(grid) == "complex"


def test_colspan_makes_a_table_complex_even_if_narrow() -> None:
    grid = _grid([[_cell(col_span=2)]], column_count=2)

    assert classify_table_complexity(grid) == "complex"


def test_complex_takes_priority_over_wide() -> None:
    row = [_cell(row_span=2)] + [_cell() for _ in range(7)]
    grid = _grid([row], column_count=8)

    assert classify_table_complexity(grid) == "complex"
