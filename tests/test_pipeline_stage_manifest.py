from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.pipeline.stage_manifest import (
    StageManifestError,
    extract_status,
    read_manifest_payload,
    validate_stage_manifest_payload,
    write_stage_manifest_payload,
)

_VALID_PAYLOAD: dict[str, object] = {
    "schema_version": 1,
    "stage": "30-ingest",
    "stage_version": 1,
    "status": "complete",
    "run_id": "test-run",
    "started_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    "completed_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    "inputs": {},
    "outputs": [],
    "metrics": {},
    "software": {"git_commit": None, "app_image_digest": None, "toolchain_image_digest": None},
}


def test_validate_stage_manifest_payload_accepts_valid_envelope() -> None:
    validate_stage_manifest_payload(_VALID_PAYLOAD)


def test_validate_stage_manifest_payload_rejects_non_object() -> None:
    with pytest.raises(StageManifestError, match="JSON object"):
        validate_stage_manifest_payload(["not", "an", "object"])


@pytest.mark.parametrize("missing_key", list(_VALID_PAYLOAD.keys()))
def test_validate_stage_manifest_payload_rejects_missing_required_field(missing_key: str) -> None:
    payload = dict(_VALID_PAYLOAD)
    del payload[missing_key]

    with pytest.raises(StageManifestError, match="missing required field"):
        validate_stage_manifest_payload(payload)


def test_validate_stage_manifest_payload_rejects_invalid_status() -> None:
    payload = dict(_VALID_PAYLOAD)
    payload["status"] = "bogus"

    with pytest.raises(StageManifestError, match="status must be one of"):
        validate_stage_manifest_payload(payload)


@pytest.mark.parametrize("status", ["running", "complete", "failed", "interrupted", "invalid"])
def test_validate_stage_manifest_payload_accepts_all_status_enum_values(status: str) -> None:
    payload = dict(_VALID_PAYLOAD)
    payload["status"] = status

    validate_stage_manifest_payload(payload)


def test_validate_stage_manifest_payload_rejects_empty_stage() -> None:
    payload = dict(_VALID_PAYLOAD)
    payload["stage"] = ""

    with pytest.raises(StageManifestError, match="'stage'"):
        validate_stage_manifest_payload(payload)


def test_write_and_read_manifest_payload_round_trips(tmp_path: Path) -> None:
    destination = tmp_path / "manifest.json"

    write_stage_manifest_payload(_VALID_PAYLOAD, destination)
    payload = read_manifest_payload(destination)

    assert payload is not None
    assert payload["status"] == "complete"
    assert extract_status(payload, destination) == "complete"


def test_read_manifest_payload_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_manifest_payload(tmp_path / "missing.json") is None


def test_read_manifest_payload_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("not json", encoding="utf-8")

    with pytest.raises(StageManifestError, match="cannot read existing manifest"):
        read_manifest_payload(path)


def test_write_stage_manifest_payload_rejects_invalid_payload(tmp_path: Path) -> None:
    payload = dict(_VALID_PAYLOAD)
    payload["status"] = "bogus"

    with pytest.raises(StageManifestError, match="status must be one of"):
        write_stage_manifest_payload(payload, tmp_path / "manifest.json")


def test_write_stage_manifest_payload_is_valid_json_on_disk(tmp_path: Path) -> None:
    destination = tmp_path / "manifest.json"

    write_stage_manifest_payload(_VALID_PAYLOAD, destination)

    on_disk = json.loads(destination.read_text(encoding="utf-8"))
    assert on_disk == _VALID_PAYLOAD
