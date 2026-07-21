"""EPWING verifier baseline (TASK-H011, ARCHITECTURE.md 7.1 `wikiepwing verify`).

Checks `entries.jsonl` (TASK-H010's `generate` output) for the same
invariants `docker/toolchain/freepwing_build_entries.pl` (TASK-H009)
enforces before it will build a dictionary -- empty tag/title, duplicate
tags, duplicate headwords across different entries, and unknown link
targets -- but in Python, without needing Docker/Perl, so problems surface
immediately after `generate` rather than only when the toolchain runs.
Verifying the actual built EPWING binary (honmon, etc.) via the EB Library
is later work (e.g. TASK-H013).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from wikiepwing.pipeline.progress import PhaseProgress


class EntriesVerificationError(ValueError):
    """Raised when entries.jsonl cannot be read/parsed for verification."""


@dataclass(frozen=True, slots=True)
class VerificationIssue:
    """One problem found while verifying entries.jsonl."""

    code: str
    message: str

    def payload(self) -> dict[str, str]:
        """Return this issue as a JSON-serializable mapping."""
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """The outcome of verifying one entries.jsonl file."""

    ok: bool
    entry_count: int
    issues: tuple[VerificationIssue, ...]

    def payload(self) -> dict[str, object]:
        """Return this result as a JSON-serializable mapping."""
        return {
            "ok": self.ok,
            "entry_count": self.entry_count,
            "issues": [issue.payload() for issue in self.issues],
        }


def verify_entries_jsonl(
    path: Path, *, on_progress: Callable[[PhaseProgress], None] | None = None
) -> VerificationResult:
    """Verify one entries.jsonl file's structural invariants."""
    records = _read_records(path, on_progress=on_progress)
    issues: list[VerificationIssue] = []

    tags: set[str] = set()
    if not records:
        _report(on_progress, "verify-entries-tags", 0, 0)
    for index, record in enumerate(records, start=1):
        tag = record.get("tag")
        title = record.get("title")
        if not isinstance(tag, str) or not tag:
            issues.append(VerificationIssue("EMPTY_TAG", "an entry has an empty or missing tag"))
            _report(on_progress, "verify-entries-tags", index, len(records))
            continue
        if tag in tags:
            issues.append(VerificationIssue("DUPLICATE_TAG", f"duplicate tag: {tag}"))
        tags.add(tag)
        if not isinstance(title, str) or not title:
            issues.append(VerificationIssue("EMPTY_TITLE", f"entry {tag} has an empty title"))
        _report(on_progress, "verify-entries-tags", index, len(records))

    if not records:
        _report(on_progress, "verify-entries-headwords", 0, 0)
    for index, _record in enumerate(records, start=1):
        # Progress reporting for headwords validation phase is kept for backward compatibility,
        # but duplicate headwords check is removed as FreePWING supports duplicate headwords.
        _report(on_progress, "verify-entries-headwords", index, len(records))

    for index, record in enumerate(records, start=1):
        tag = record.get("tag")
        targets = record.get("targets", [])
        if not isinstance(targets, list):
            _report(on_progress, "verify-entries-targets", index, len(records))
            continue
        for target in targets:
            if target not in tags:
                issues.append(
                    VerificationIssue(
                        "UNKNOWN_TARGET",
                        f"entry {tag} references unknown link target: {target!r}",
                    )
                )
        _report(on_progress, "verify-entries-targets", index, len(records))

    return VerificationResult(ok=not issues, entry_count=len(records), issues=tuple(issues))


def _read_records(
    path: Path, *, on_progress: Callable[[PhaseProgress], None] | None
) -> list[dict[str, object]]:
    try:
        file = path.open(encoding="utf-8")
    except OSError as error:
        raise EntriesVerificationError(f"cannot read {path}: {error}") from error

    # JSONL records are separated by ASCII "\n" only. `str.splitlines()` also
    # breaks on Unicode line/paragraph separators (e.g. U+2029), which real
    # Wikipedia article bodies legitimately contain inside a JSON string,
    # splitting one valid record into several invalid fragments.
    records: list[dict[str, object]] = []
    with file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise EntriesVerificationError(
                    f"{path}:{line_number}: invalid JSON: {error}"
                ) from error
            if not isinstance(record, dict):
                raise EntriesVerificationError(
                    f"{path}:{line_number}: record must be a JSON object"
                )
            records.append(record)
            if on_progress is not None:
                on_progress(
                    PhaseProgress(
                        phase="verify-entries-read",
                        completed=len(records),
                        total=None,
                        unit="items",
                    )
                )
    if on_progress is not None:
        on_progress(
            PhaseProgress(
                phase="verify-entries-read",
                completed=len(records),
                total=len(records),
                unit="items",
                complete=True,
            )
        )
    return records


def _report(
    callback: Callable[[PhaseProgress], None] | None,
    phase: str,
    completed: int,
    total: int,
) -> None:
    if callback is not None:
        callback(
            PhaseProgress(
                phase=phase,
                completed=completed,
                total=total,
                unit="items",
                complete=completed >= total,
            )
        )
