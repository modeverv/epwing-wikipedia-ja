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
from dataclasses import dataclass
from pathlib import Path


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


def verify_entries_jsonl(path: Path) -> VerificationResult:
    """Verify one entries.jsonl file's structural invariants."""
    records = _read_records(path)
    issues: list[VerificationIssue] = []

    tags: set[str] = set()
    for record in records:
        tag = record.get("tag")
        title = record.get("title")
        if not isinstance(tag, str) or not tag:
            issues.append(VerificationIssue("EMPTY_TAG", "an entry has an empty or missing tag"))
            continue
        if tag in tags:
            issues.append(VerificationIssue("DUPLICATE_TAG", f"duplicate tag: {tag}"))
        tags.add(tag)
        if not isinstance(title, str) or not title:
            issues.append(VerificationIssue("EMPTY_TITLE", f"entry {tag} has an empty title"))

    headword_owners: dict[str, str] = {}
    for record in records:
        tag = record.get("tag")
        if not isinstance(tag, str) or not tag:
            continue
        aliases = record.get("aliases", [])
        headwords: list[object] = [record.get("title")]
        if isinstance(aliases, list):
            headwords.extend(aliases)
        for headword in headwords:
            if not isinstance(headword, str) or not headword:
                continue
            owner = headword_owners.get(headword)
            if owner is not None and owner != tag:
                issues.append(
                    VerificationIssue(
                        "DUPLICATE_HEADWORD",
                        f"headword {headword!r} is used by both {owner} and {tag}",
                    )
                )
            else:
                headword_owners[headword] = tag

    for record in records:
        tag = record.get("tag")
        targets = record.get("targets", [])
        if not isinstance(targets, list):
            continue
        for target in targets:
            if target not in tags:
                issues.append(
                    VerificationIssue(
                        "UNKNOWN_TARGET",
                        f"entry {tag} references unknown link target: {target!r}",
                    )
                )

    return VerificationResult(ok=not issues, entry_count=len(records), issues=tuple(issues))


def _read_records(path: Path) -> list[dict[str, object]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise EntriesVerificationError(f"cannot read {path}: {error}") from error

    # JSONL records are separated by ASCII "\n" only. `str.splitlines()` also
    # breaks on Unicode line/paragraph separators (e.g. U+2029), which real
    # Wikipedia article bodies legitimately contain inside a JSON string,
    # splitting one valid record into several invalid fragments.
    records: list[dict[str, object]] = []
    for line_number, line in enumerate(text.split("\n"), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise EntriesVerificationError(
                f"{path}:{line_number}: invalid JSON: {error}"
            ) from error
        if not isinstance(record, dict):
            raise EntriesVerificationError(f"{path}:{line_number}: record must be a JSON object")
        records.append(record)
    return records
