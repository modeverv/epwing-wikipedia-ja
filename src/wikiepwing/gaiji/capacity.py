"""Limit an already generated gaiji corpus to FreePWING's code-space capacity."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from wikiepwing.gaiji.code_assignment import MAX_GAIJI_PER_WIDTH
from wikiepwing.gaiji.unrepresentable import unrepresentable_fallback
from wikiepwing.pipeline.atomic_write import atomic_write_text

_TOKEN = re.compile(rb"@@GAIJI:((?:narrow|wide)-[0-9]+)@@")
_PROGRESS_BYTES = 256 * 1024 * 1024


class GaijiCapacityError(RuntimeError):
    """Raised when existing generated artifacts cannot be limited safely."""


@dataclass(frozen=True, slots=True)
class CapacityPlan:
    """Selected and overflow gaiji codes from one generated registry."""

    selected_codes: frozenset[str]
    overflow_fallbacks: dict[str, str]
    selected_by_width: dict[str, int]
    overflow_by_width: dict[str, int]
    overflow_occurrences_by_width: dict[str, int]


@dataclass(frozen=True, slots=True)
class RewriteMetrics:
    """Token counts observed while rewriting entries JSONL."""

    bytes_read: int
    selected_tokens: int
    overflow_tokens: int


def plan_capacity(database_path: Path, *, max_per_width: int) -> CapacityPlan:
    """Select frequent gaiji per width with deterministic Unicode tie-breaking."""
    if max_per_width < 0:
        raise GaijiCapacityError("max_per_width must be non-negative")
    connection = sqlite3.connect(database_path)
    try:
        rows = connection.execute(
            "SELECT assigned_code, sequence, width_class, usage_count FROM gaiji "
            "ORDER BY width_class, usage_count DESC, sequence"
        ).fetchall()
    finally:
        connection.close()

    selected_codes: set[str] = set()
    overflow_fallbacks: dict[str, str] = {}
    selected_by_width = {"narrow": 0, "wide": 0}
    overflow_by_width = {"narrow": 0, "wide": 0}
    overflow_occurrences_by_width = {"narrow": 0, "wide": 0}
    for assigned_code, sequence, width_class, usage_count in rows:
        width = str(width_class)
        if width not in selected_by_width:
            raise GaijiCapacityError(f"invalid width_class in registry: {width!r}")
        code = str(assigned_code)
        if selected_by_width[width] < max_per_width:
            selected_codes.add(code)
            selected_by_width[width] += 1
        else:
            overflow_fallbacks[code] = unrepresentable_fallback(str(sequence))
            overflow_by_width[width] += 1
            overflow_occurrences_by_width[width] += int(usage_count)
    return CapacityPlan(
        selected_codes=frozenset(selected_codes),
        overflow_fallbacks=overflow_fallbacks,
        selected_by_width=selected_by_width,
        overflow_by_width=overflow_by_width,
        overflow_occurrences_by_width=overflow_occurrences_by_width,
    )


def rewrite_entries_jsonl(source: Path, destination: Path, *, plan: CapacityPlan) -> RewriteMetrics:
    """Stream JSONL, replacing only overflow gaiji tokens with codepoint fallbacks."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    selected = {code.encode("ascii") for code in plan.selected_codes}
    overflow = {
        code.encode("ascii"): fallback.encode("ascii")
        for code, fallback in plan.overflow_fallbacks.items()
    }
    selected_tokens = 0
    overflow_tokens = 0
    bytes_read = 0
    next_progress = _PROGRESS_BYTES

    def replace(match: re.Match[bytes]) -> bytes:
        nonlocal selected_tokens, overflow_tokens
        code = match.group(1)
        if code in selected:
            selected_tokens += 1
            return match.group(0)
        replacement = overflow.get(code)
        if replacement is None:
            raise GaijiCapacityError(f"entries references unknown gaiji code: {code!r}")
        overflow_tokens += 1
        return replacement

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with source.open("rb") as input_file, os.fdopen(descriptor, "wb") as output_file:
            for line in input_file:
                bytes_read += len(line)
                output_file.write(_TOKEN.sub(replace, line))
                if bytes_read >= next_progress:
                    print(f"phase=gaiji-capacity-rewrite bytes={bytes_read}", file=sys.stderr)
                    next_progress += _PROGRESS_BYTES
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary, destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return RewriteMetrics(
        bytes_read=bytes_read,
        selected_tokens=selected_tokens,
        overflow_tokens=overflow_tokens,
    )


def write_limited_gaiji_directory(
    source: Path, destination: Path, *, selected_codes: frozenset[str]
) -> None:
    """Copy selected XBM files and emit matching FreePWING definition lists."""
    if destination.exists():
        raise GaijiCapacityError(f"destination gaiji directory already exists: {destination}")
    destination.mkdir(parents=True)
    for list_name in ("halfchars.txt", "fullchars.txt"):
        source_list = source / list_name
        selected_lines: list[str] = []
        for line in source_list.read_text(encoding="ascii").splitlines():
            code, filename = line.split(maxsplit=1)
            if code not in selected_codes:
                continue
            source_bitmap = source / filename
            if not source_bitmap.is_file():
                raise GaijiCapacityError(f"missing gaiji bitmap: {source_bitmap}")
            shutil.copyfile(source_bitmap, destination / filename)
            selected_lines.append(f"{code} {filename}")
        atomic_write_text(
            destination / list_name,
            "".join(f"{line}\n" for line in selected_lines),
        )


def limit_existing_artifacts(
    *,
    entries_source: Path,
    database_path: Path,
    gaiji_source: Path,
    entries_destination: Path,
    gaiji_destination: Path,
    report_path: Path,
    max_per_width: int = MAX_GAIJI_PER_WIDTH,
) -> RewriteMetrics:
    """Create capacity-safe entries and gaiji files from a completed generate output."""
    plan = plan_capacity(database_path, max_per_width=max_per_width)
    metrics = rewrite_entries_jsonl(entries_source, entries_destination, plan=plan)
    write_limited_gaiji_directory(
        gaiji_source, gaiji_destination, selected_codes=plan.selected_codes
    )
    report = {
        "schema_version": 1,
        "max_per_width": max_per_width,
        "selected_by_width": plan.selected_by_width,
        "overflow_by_width": plan.overflow_by_width,
        "overflow_occurrences_by_width": plan.overflow_occurrences_by_width,
        "bytes_read": metrics.bytes_read,
        "selected_tokens": metrics.selected_tokens,
        "overflow_tokens": metrics.overflow_tokens,
    }
    atomic_write_text(
        report_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return metrics


def main() -> int:
    """Run the capacity limiter as a small recovery/build utility."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--entries-source", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--gaiji-source", type=Path, required=True)
    parser.add_argument("--entries-output", type=Path, required=True)
    parser.add_argument("--gaiji-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--max-per-width", type=int, default=MAX_GAIJI_PER_WIDTH)
    arguments = parser.parse_args()
    limit_existing_artifacts(
        entries_source=arguments.entries_source,
        database_path=arguments.database,
        gaiji_source=arguments.gaiji_source,
        entries_destination=arguments.entries_output,
        gaiji_destination=arguments.gaiji_output,
        report_path=arguments.report,
        max_per_width=arguments.max_per_width,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
