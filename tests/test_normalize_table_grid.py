from __future__ import annotations

from wikiepwing.normalize.table_grid import normalize_table_spans
from wikiepwing.normalize.tables import RawTable, RawTableCell, RawTableRow


def _cell(row_span: int = 1, col_span: int = 1) -> RawTableCell:
    return RawTableCell(content=(), row_span=row_span, col_span=col_span, is_header=False)


def test_simple_grid_has_sequential_columns() -> None:
    table = RawTable(
        caption=(),
        rows=(
            RawTableRow(cells=(_cell(), _cell())),
            RawTableRow(cells=(_cell(), _cell())),
        ),
        source_class_names=(),
    )

    normalized = normalize_table_spans(table)

    assert [cell.col_index for cell in normalized.rows[0]] == [0, 1]
    assert [cell.col_index for cell in normalized.rows[1]] == [0, 1]
    assert normalized.column_count == 2


def test_colspan_shifts_later_cell_in_same_row() -> None:
    table = RawTable(
        caption=(),
        rows=(RawTableRow(cells=(_cell(col_span=2), _cell())),),
        source_class_names=(),
    )

    normalized = normalize_table_spans(table)

    assert normalized.rows[0][0].col_index == 0
    assert normalized.rows[0][1].col_index == 2
    assert normalized.column_count == 3


def test_rowspan_pushes_next_row_cell_past_occupied_column() -> None:
    table = RawTable(
        caption=(),
        rows=(
            RawTableRow(cells=(_cell(row_span=2), _cell())),
            RawTableRow(cells=(_cell(),)),
        ),
        source_class_names=(),
    )

    normalized = normalize_table_spans(table)

    assert [cell.col_index for cell in normalized.rows[0]] == [0, 1]
    # row 1 has only one explicit cell, but column 0 is occupied by the
    # rowspan from row 0, so it lands in column 1.
    assert normalized.rows[1][0].col_index == 1


def test_rowspan_and_colspan_combined_occupy_a_rectangle() -> None:
    table = RawTable(
        caption=(),
        rows=(
            RawTableRow(cells=(_cell(row_span=2, col_span=2), _cell())),
            RawTableRow(cells=(_cell(),)),
        ),
        source_class_names=(),
    )

    normalized = normalize_table_spans(table)

    # row 0: origin cell spans cols 0-1; the second cell lands at col 2.
    assert [cell.col_index for cell in normalized.rows[0]] == [0, 2]
    # row 1: cols 0-1 are occupied by the rowspan+colspan cell, so the
    # single explicit cell lands at col 2.
    assert normalized.rows[1][0].col_index == 2


def test_rowspan_stops_after_its_span_expires() -> None:
    table = RawTable(
        caption=(),
        rows=(
            RawTableRow(cells=(_cell(row_span=2), _cell())),
            RawTableRow(cells=(_cell(),)),
            RawTableRow(cells=(_cell(), _cell())),
        ),
        source_class_names=(),
    )

    normalized = normalize_table_spans(table)

    assert normalized.rows[1][0].col_index == 1
    # row 2: the rowspan from row 0 has expired, so both cells start fresh.
    assert [cell.col_index for cell in normalized.rows[2]] == [0, 1]


def test_column_count_accounts_for_the_widest_row() -> None:
    table = RawTable(
        caption=(),
        rows=(
            RawTableRow(cells=(_cell(),)),
            RawTableRow(cells=(_cell(), _cell(), _cell())),
        ),
        source_class_names=(),
    )

    normalized = normalize_table_spans(table)

    assert normalized.column_count == 3


def test_empty_table_has_zero_columns() -> None:
    table = RawTable(caption=(), rows=(), source_class_names=())

    normalized = normalize_table_spans(table)

    assert normalized.column_count == 0
    assert normalized.rows == ()


def test_caption_and_class_names_are_preserved() -> None:
    table = RawTable(
        caption=(), rows=(RawTableRow(cells=(_cell(),)),), source_class_names=("wikitable",)
    )

    normalized = normalize_table_spans(table)

    assert normalized.source_class_names == ("wikitable",)
