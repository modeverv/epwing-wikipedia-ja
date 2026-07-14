"""Stage manifest schema (TASK-I001, DATA_CONTRACTS.md 3 "Stage manifest contract").

Consolidates the manifest read/parse/atomic-write logic that
`wikiepwing.ingest.orchestrate`, `wikiepwing.normalize.orchestrate`, and
`wikiepwing.render.generate` each implemented independently (near-identical
copies). `validate_stage_manifest_payload` enforces the envelope shape
DATA_CONTRACTS.md 3 defines (required fields, `status` enum); per-stage
`metrics` shapes are intentionally left unvalidated here since each stage
defines its own.

Each orchestrate module keeps its own `read_manifest_status`/error type for
backward compatibility (existing callers match on e.g. `IngestError`), but
delegates the actual file I/O and validation to this module.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Literal, cast

STAGE_MANIFEST_SCHEMA_VERSION = 1

StageStatus = Literal["running", "complete", "failed", "interrupted", "invalid"]
_STAGE_STATUSES = ("running", "complete", "failed", "interrupted", "invalid")

_REQUIRED_FIELDS = (
    "schema_version",
    "stage",
    "stage_version",
    "status",
    "run_id",
    "started_at",
    "completed_at",
    "inputs",
    "outputs",
    "metrics",
    "software",
)


class StageManifestError(ValueError):
    """Raised when a stage manifest payload is missing or violates the schema."""


def validate_stage_manifest_payload(payload: object) -> None:
    """Validate `payload` against DATA_CONTRACTS.md 3's Stage Manifest envelope."""
    if not isinstance(payload, dict):
        raise StageManifestError("stage manifest must be a JSON object")
    fields = cast(dict[str, object], payload)
    for key in _REQUIRED_FIELDS:
        if key not in fields:
            raise StageManifestError(f"stage manifest is missing required field: {key}")
    if not isinstance(fields["stage"], str) or not fields["stage"]:
        raise StageManifestError("stage manifest field 'stage' must be a non-empty string")
    if not isinstance(fields["run_id"], str) or not fields["run_id"]:
        raise StageManifestError("stage manifest field 'run_id' must be a non-empty string")
    status = fields["status"]
    if status not in _STAGE_STATUSES:
        raise StageManifestError(
            f"stage manifest status must be one of {_STAGE_STATUSES}: {status!r}"
        )
    if not isinstance(fields["inputs"], dict):
        raise StageManifestError("stage manifest field 'inputs' must be an object")
    if not isinstance(fields["outputs"], list):
        raise StageManifestError("stage manifest field 'outputs' must be an array")
    if not isinstance(fields["software"], dict):
        raise StageManifestError("stage manifest field 'software' must be an object")


def read_manifest_payload(manifest_path: Path) -> dict[str, object] | None:
    """Read a manifest file's JSON object payload, or None if it doesn't exist.

    Deliberately does *not* run full envelope validation: callers checking
    whether a previous run is still "running" only need the `status` field,
    and existing (and test) manifests are sometimes minimal partial objects.
    Use `validate_stage_manifest_payload` separately where full compliance
    matters (e.g. before writing).
    """
    if not manifest_path.is_file():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StageManifestError(
            f"cannot read existing manifest {manifest_path}: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise StageManifestError(f"existing manifest {manifest_path} must be a JSON object")
    return cast(dict[str, object], payload)


def extract_status(payload: dict[str, object], manifest_path: Path) -> str:
    """Return a validated manifest payload's `status` field."""
    status = payload.get("status")
    if not isinstance(status, str) or not status:
        raise StageManifestError(f"existing manifest {manifest_path} has no valid status field")
    return status


def write_stage_manifest_payload(payload: dict[str, object], destination: Path) -> None:
    """Validate and atomically write a manifest payload to `destination`."""
    validate_stage_manifest_payload(payload)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", delete=False
    )
    try:
        temp_path = Path(handle.name)
        handle.write(text.encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    os.replace(temp_path, destination)
