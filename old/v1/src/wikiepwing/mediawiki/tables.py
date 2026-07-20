"""Safe, readable fallback for basic MediaWiki tables."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TableResult:
    rows: tuple[tuple[str, ...], ...]
    diagnostic: str | None = None


def parse_table(source: str, maximum_rows: int = 100) -> TableResult:
    """Extract simple rows/cells, retaining text rather than CSS or attributes."""
    if not source.startswith("{|") or not source.rstrip().endswith("|}"):
        return TableResult((), "TABLE_PARSE_FAILED")
    rows: list[tuple[str, ...]] = []
    cells: list[str] = []
    for line in source.splitlines()[1:-1]:
        stripped = line.strip()
        if stripped.startswith("|-"):
            if cells:
                rows.append(tuple(cells))
                cells.clear()
        elif stripped.startswith("!") or stripped.startswith("|"):
            content = stripped[1:]
            cells.extend(part.split("|", 1)[-1].strip() for part in re.split(r"!!|\|\|", content))
        if len(rows) >= maximum_rows:
            return TableResult(tuple(rows), "TABLE_TRUNCATED")
    if cells:
        rows.append(tuple(cells))
    return TableResult(tuple(rows))


def render_table(result: TableResult) -> str:
    """Render each row compactly so narrow readers retain all cell content."""
    return "\n".join(" | ".join(row) for row in result.rows)
