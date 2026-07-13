from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import jsonschema
import pytest

from wikiepwing.doctor import _path_check

SCHEMA_PATH = Path("schemas/doctor-report.schema.json")


def _write_override(tmp_path: Path) -> Path:
    paths = {
        name: tmp_path / name
        for name in ("sources", "reference", "work", "cache", "output", "reports", "logs")
    }
    for path in paths.values():
        path.mkdir()
    paths["reference"].chmod(0o555)

    override = tmp_path / "doctor.toml"
    path_lines = "\n".join(f"{name} = {json.dumps(str(path))}" for name, path in paths.items())
    override.write_text(
        f"""
[paths]
{path_lines}

[resources]
minimum_free_disk_gib = 0
""",
        encoding="utf-8",
    )
    return override


def _run_doctor(override: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.update({"TZ": "UTC", "WIKIEPWING_CONTAINER": "1"})
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "wikiepwing.cli",
            "doctor",
            "--config",
            str(override),
            *arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def _load_schema() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def test_doctor_json_matches_schema(tmp_path: Path) -> None:
    result = _run_doctor(_write_override(tmp_path), "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    jsonschema.Draft202012Validator(
        _load_schema(), format_checker=jsonschema.FormatChecker()
    ).validate(payload)
    assert payload["ok"] is True
    names = {check["name"] for check in payload["checks"]}
    assert {
        "architecture",
        "locale",
        "timezone",
        "free_disk",
        "configuration",
        "path:sources",
        "tool:uv",
    } <= names


def test_doctor_human_output_is_readable(tmp_path: Path) -> None:
    result = _run_doctor(_write_override(tmp_path))

    assert result.returncode == 0, result.stderr
    assert "Doctor: OK" in result.stdout
    assert "[PASS] environment/architecture" in result.stdout
    assert "[WARNING] tool/fpwmake" in result.stdout


def test_doctor_configuration_error_uses_exit_two_and_valid_json(tmp_path: Path) -> None:
    override = tmp_path / "invalid.toml"
    override.write_text("unknown = true\n", encoding="utf-8")

    result = _run_doctor(override, "--json")

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    jsonschema.Draft202012Validator(
        _load_schema(), format_checker=jsonschema.FormatChecker()
    ).validate(payload)
    assert payload["ok"] is False
    assert payload["checks"][0]["name"] == "configuration"


def test_doctor_required_check_failure_uses_exit_one(tmp_path: Path) -> None:
    override = _write_override(tmp_path)
    (tmp_path / "work").rmdir()

    result = _run_doctor(override, "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    jsonschema.Draft202012Validator(
        _load_schema(), format_checker=jsonschema.FormatChecker()
    ).validate(payload)
    assert payload["ok"] is False
    failed = {check["name"] for check in payload["checks"] if check["status"] == "fail"}
    assert {"path:work", "free_disk"} <= failed


def test_doctor_checks_read_only_reference_without_opening_a_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reference = tmp_path / "reference"
    reference.mkdir(mode=0o555)
    original_open = Path.open

    def guarded_open(path: Path, mode: str = "r", *args: object, **kwargs: object) -> Any:
        if path.parent == reference and any(flag in mode for flag in "wax+"):
            raise AssertionError("doctor attempted to write inside reference")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    result = _path_check("reference", reference, expected_writable=False)

    assert result.status == "pass"
    assert result.data["writable"] is False
