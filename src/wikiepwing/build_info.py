"""BUILD-INFO.json generation (TASK-S001, ARCHITECTURE.md 26.3/28.1).

26.3's "生成物にBUILD-INFO.jsonを添付します" (attach BUILD-INFO.json to
build artifacts) and 28.1's "BUILD-INFOにWikimedia projectとsnapshot版
を記載" (record the Wikimedia project and snapshot version) are covered
by reusing `SourceLock`'s already-resolved project/snapshot fields
(TASK-D-era `source/lockfile.py`) rather than re-deriving them, plus a
`software` block matching the stage manifest's own `git_commit`/
`app_image_digest`/`toolchain_image_digest` shape (DATA_CONTRACTS.md 3)
for consistency across every provenance record this project writes.

`DATA_CONTRACTS.md` 12 places `jawiki-<snapshot>-<profile>-BUILD-INFO.json`
alongside each profile's packaged artifact; this module only builds and
writes that one file, not the package/archive itself.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from wikiepwing.pipeline.atomic_write import atomic_write_text
from wikiepwing.source.lockfile import SourceLock

BUILD_INFO_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class SoftwareProvenance:
    """The software identity that produced a build (mirrors stage manifest's `software`)."""

    git_commit: str
    app_image_digest: str | None
    toolchain_image_digest: str | None


def build_build_info(
    source_lock: SourceLock,
    *,
    profile: str,
    built_at: datetime,
    software: SoftwareProvenance,
) -> dict[str, object]:
    """Return BUILD-INFO.json's payload for one packaged build artifact."""
    if built_at.tzinfo is None:
        raise ValueError("built_at must be timezone-aware")
    return {
        "schema_version": BUILD_INFO_SCHEMA_VERSION,
        "project": source_lock.project,
        "snapshot_identifier": source_lock.snapshot_identifier,
        "snapshot_version": source_lock.snapshot_version,
        "snapshot_date_modified": _format_datetime(source_lock.date_modified),
        "profile": profile,
        "built_at": _format_datetime(built_at),
        "software": {
            "git_commit": software.git_commit,
            "app_image_digest": software.app_image_digest,
            "toolchain_image_digest": software.toolchain_image_digest,
        },
    }


def write_build_info(payload: dict[str, object], output_path: Path) -> None:
    """Write `payload` as BUILD-INFO.json, atomically."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        output_path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def _format_datetime(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")
