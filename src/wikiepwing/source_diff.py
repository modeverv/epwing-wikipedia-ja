"""Source snapshot diff and update report (TASK-S006, PLAN.md 29's `wikiepwing update`).

Compares a newly acquired `SourceLock` against the previous one (if any) to
report what changed between Snapshot versions: chunk additions/removals,
chunks whose content changed (same `chunk_identifier`, different `sha256`),
and the total size delta. Media/math cache reuse is already handled by their
own content-hash-keyed caches and needs no extra logic here; old run/output
cleanup is handled by `clean.py` (TASK-S008) and the pipeline commands
respectively -- this module only computes and records the diff.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from wikiepwing.pipeline.atomic_write import atomic_write_text
from wikiepwing.source.lockfile import SourceLock

UPDATE_REPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class SourceDiff:
    """The difference between a previous and newly acquired `SourceLock`."""

    previous_snapshot_version: str | None
    new_snapshot_version: str
    version_changed: bool
    added_chunk_identifiers: tuple[str, ...]
    removed_chunk_identifiers: tuple[str, ...]
    changed_chunk_identifiers: tuple[str, ...]
    unchanged_chunk_count: int
    previous_total_size_bytes: int | None
    new_total_size_bytes: int
    size_delta_bytes: int

    def payload(self) -> dict[str, object]:
        """Return this diff's JSON-serializable representation."""
        return {
            "previous_snapshot_version": self.previous_snapshot_version,
            "new_snapshot_version": self.new_snapshot_version,
            "version_changed": self.version_changed,
            "added_chunk_identifiers": list(self.added_chunk_identifiers),
            "removed_chunk_identifiers": list(self.removed_chunk_identifiers),
            "changed_chunk_identifiers": list(self.changed_chunk_identifiers),
            "unchanged_chunk_count": self.unchanged_chunk_count,
            "previous_total_size_bytes": self.previous_total_size_bytes,
            "new_total_size_bytes": self.new_total_size_bytes,
            "size_delta_bytes": self.size_delta_bytes,
        }


def compute_source_diff(previous: SourceLock | None, new: SourceLock) -> SourceDiff:
    """Compute the diff between `previous` (or `None` for a first acquire) and `new`."""
    new_total_size_bytes = sum(file.size_bytes for file in new.files)
    if previous is None:
        return SourceDiff(
            previous_snapshot_version=None,
            new_snapshot_version=new.snapshot_version,
            version_changed=True,
            added_chunk_identifiers=tuple(file.chunk_identifier for file in new.files),
            removed_chunk_identifiers=(),
            changed_chunk_identifiers=(),
            unchanged_chunk_count=0,
            previous_total_size_bytes=None,
            new_total_size_bytes=new_total_size_bytes,
            size_delta_bytes=new_total_size_bytes,
        )

    previous_by_chunk = {file.chunk_identifier: file for file in previous.files}
    new_by_chunk = {file.chunk_identifier: file for file in new.files}
    previous_total_size_bytes = sum(file.size_bytes for file in previous.files)

    added = tuple(identifier for identifier in new_by_chunk if identifier not in previous_by_chunk)
    removed = tuple(
        identifier for identifier in previous_by_chunk if identifier not in new_by_chunk
    )
    changed = tuple(
        identifier
        for identifier in new_by_chunk
        if identifier in previous_by_chunk
        and new_by_chunk[identifier].sha256 != previous_by_chunk[identifier].sha256
    )
    unchanged_chunk_count = len(new_by_chunk) - len(added) - len(changed)

    return SourceDiff(
        previous_snapshot_version=previous.snapshot_version,
        new_snapshot_version=new.snapshot_version,
        version_changed=previous.snapshot_version != new.snapshot_version,
        added_chunk_identifiers=added,
        removed_chunk_identifiers=removed,
        changed_chunk_identifiers=changed,
        unchanged_chunk_count=unchanged_chunk_count,
        previous_total_size_bytes=previous_total_size_bytes,
        new_total_size_bytes=new_total_size_bytes,
        size_delta_bytes=new_total_size_bytes - previous_total_size_bytes,
    )


def build_update_report(diff: SourceDiff, *, updated_at: datetime) -> dict[str, object]:
    """Build the JSON-serializable update report payload for `diff`."""
    if updated_at.tzinfo is None:
        raise ValueError("updated_at must be timezone-aware")
    return {
        "schema_version": UPDATE_REPORT_SCHEMA_VERSION,
        "updated_at": updated_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "diff": diff.payload(),
    }


def write_update_report(payload: dict[str, object], output_path: Path) -> None:
    """Atomically write an update report payload as pretty-printed, sorted-key JSON."""
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    atomic_write_text(output_path, text)
