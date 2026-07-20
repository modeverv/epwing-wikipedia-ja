"""Environment preflight checks for the containerized builder."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

from wikiepwing.config import ConfigurationError, load_config


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _check_writable(directory: Path) -> CheckResult:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".wikiepwing-doctor-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as error:
        return CheckResult(f"writable:{directory}", False, str(error))
    return CheckResult(f"writable:{directory}", True, "writable")


def run_doctor(config_path: Path) -> tuple[CheckResult, ...]:
    """Run deterministic local preflight checks without altering build data."""
    try:
        config = load_config(config_path)
    except ConfigurationError as error:
        return (CheckResult("configuration", False, str(error)),)
    results = [
        CheckResult("configuration", True, f"loaded {config_path}"),
        CheckResult("non_root", os.geteuid() != 0, f"uid={os.geteuid()}"),
    ]
    directories = (config.paths.data_dir, config.paths.output_dir, config.paths.reports_dir)
    results.extend(_check_writable(directory) for directory in directories)
    return tuple(results)


def doctor_payload(results: tuple[CheckResult, ...]) -> dict[str, object]:
    """Return the stable machine-readable representation of doctor results."""
    return {
        "ok": all(result.ok for result in results),
        "checks": [asdict(result) for result in results],
    }
