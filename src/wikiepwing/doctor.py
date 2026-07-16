"""Environment preflight checks for local and containerized builds."""

from __future__ import annotations

import locale
import os
import platform
import shutil
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from wikiepwing.config import AppConfig, ConfigurationError, load_config
from wikiepwing.reference.scanner import ReferencePathError, read_only_status

type CheckCategory = Literal[
    "environment", "configuration", "path", "storage", "tool", "release-gate"
]
type CheckStatus = Literal["pass", "warning", "fail"]


@dataclass(frozen=True, slots=True)
class CheckResult:
    """One stable and machine-readable preflight result."""

    name: str
    category: CheckCategory
    status: CheckStatus
    required: bool
    detail: str
    data: Mapping[str, object]

    def payload(self) -> dict[str, object]:
        """Return a JSON-serializable check representation."""
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "required": self.required,
            "detail": self.detail,
            "data": dict(self.data),
        }


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """Complete doctor result and its process exit semantics."""

    checks: tuple[CheckResult, ...]
    generated_at: datetime
    configuration_error: bool = False

    @property
    def ok(self) -> bool:
        """Whether all required checks passed."""
        return all(not check.required or check.status == "pass" for check in self.checks)

    @property
    def exit_code(self) -> int:
        """Return 2 for config errors, 1 for other required failures, else 0."""
        if self.configuration_error:
            return 2
        return 0 if self.ok else 1

    def payload(self) -> dict[str, object]:
        """Return the schema-versioned JSON representation."""
        return {
            "schema_version": 1,
            "generated_at": self.generated_at.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "ok": self.ok,
            "checks": [check.payload() for check in self.checks],
        }


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Executable expected in the current runtime."""

    name: str
    required: bool


DEFAULT_TOOLS = (
    ToolSpec("uv", True),
    ToolSpec("fpwmake", False),
    ToolSpec("ebzip", False),
    ToolSpec("ebinfo", False),
    ToolSpec("fc-match", False),
)


def run_doctor(
    default_path: Path,
    override_paths: Sequence[Path] = (),
    *,
    tools: Sequence[ToolSpec] = DEFAULT_TOOLS,
    environ: Mapping[str, str] | None = None,
) -> DoctorReport:
    """Run all preflight checks without depending on CLI rendering."""
    generated_at = datetime.now(UTC)
    try:
        config = load_config(default_path, override_paths)
    except ConfigurationError as error:
        return DoctorReport(
            checks=(
                CheckResult(
                    name="configuration",
                    category="configuration",
                    status="fail",
                    required=True,
                    detail=str(error),
                    data={"default_path": str(default_path)},
                ),
            ),
            generated_at=generated_at,
            configuration_error=True,
        )

    checks = [
        _architecture_check(),
        _python_check(),
        _locale_check(),
        _timezone_check(),
        _container_check(environ if environ is not None else os.environ),
        _configuration_check(config),
    ]
    checks.extend(_path_checks(config))
    checks.append(_free_disk_check(config))
    checks.extend(_tool_check(tool) for tool in tools)
    return DoctorReport(tuple(checks), generated_at)


def _architecture_check() -> CheckResult:
    machine = platform.machine().lower()
    supported = machine in {"aarch64", "arm64", "x86_64", "amd64"}
    return CheckResult(
        "architecture",
        "environment",
        "pass" if supported else "fail",
        True,
        f"{platform.system().lower()}/{machine}",
        {"machine": machine, "platform": platform.platform()},
    )


def _python_check() -> CheckResult:
    supported = sys.version_info[:2] == (3, 12)
    version = platform.python_version()
    return CheckResult(
        "python",
        "environment",
        "pass" if supported else "fail",
        True,
        f"Python {version}",
        {"version": version, "implementation": platform.python_implementation()},
    )


def _locale_check() -> CheckResult:
    encoding = locale.getpreferredencoding(False)
    try:
        current = locale.setlocale(locale.LC_CTYPE)
    except locale.Error as error:
        return CheckResult("locale", "environment", "fail", True, str(error), {})
    normalized = encoding.upper().replace("-", "").replace("_", "")
    return CheckResult(
        "locale",
        "environment",
        "pass" if normalized == "UTF8" else "fail",
        True,
        f"{current}; encoding={encoding}",
        {"locale": current, "preferred_encoding": encoding},
    )


def _timezone_check() -> CheckResult:
    now = datetime.now().astimezone()
    offset = now.utcoffset()
    offset_seconds = int(offset.total_seconds()) if offset is not None else None
    name = now.tzname() or "unknown"
    return CheckResult(
        "timezone",
        "environment",
        "pass" if offset_seconds == 0 else "fail",
        True,
        f"{name}; utc_offset_seconds={offset_seconds}",
        {"name": name, "utc_offset_seconds": offset_seconds},
    )


def _container_check(environ: Mapping[str, str]) -> CheckResult:
    in_container = environ.get("WIKIEPWING_CONTAINER") == "1"
    return CheckResult(
        "container",
        "environment",
        "pass" if in_container else "warning",
        False,
        "container marker present" if in_container else "container marker absent",
        {"detected": in_container},
    )


def _configuration_check(config: AppConfig) -> CheckResult:
    return CheckResult(
        "configuration",
        "configuration",
        "pass",
        True,
        f"project={config.project} profile={config.profile}",
        {
            "schema_version": config.schema_version,
            "project": config.project,
            "profile": config.profile,
            "source_files": [str(path) for path in config.source_files],
        },
    )


def _path_checks(config: AppConfig) -> tuple[CheckResult, ...]:
    configured = (
        ("sources", config.paths.sources, True),
        ("reference", config.paths.reference, False),
        ("work", config.paths.work, True),
        ("cache", config.paths.cache, True),
        ("output", config.paths.output, True),
        ("reports", config.paths.reports, True),
        ("logs", config.paths.logs, True),
    )
    return tuple(
        _path_check(name, path, expected_writable) for name, path, expected_writable in configured
    )


def _path_check(name: str, path: Path, expected_writable: bool) -> CheckResult:
    if not path.is_dir():
        return CheckResult(
            f"path:{name}",
            "path",
            "fail",
            True,
            f"directory does not exist: {path}",
            {"path": str(path), "exists": False, "expected_writable": expected_writable},
        )

    if expected_writable:
        writable, writability_detail = _probe_writable(path, name)
    else:
        try:
            read_only, writability_detail = read_only_status(path)
        except ReferencePathError as error:
            read_only = False
            writability_detail = str(error)
        writable = not read_only
    correct = writable == expected_writable
    return CheckResult(
        f"path:{name}",
        "path",
        "pass" if correct else "fail",
        True,
        f"{path}: {writability_detail}",
        {
            "path": str(path),
            "exists": True,
            "expected_writable": expected_writable,
            "writable": writable,
            "free_bytes": shutil.disk_usage(path).free,
        },
    )


def _probe_writable(path: Path, name: str) -> tuple[bool, str]:
    probe = path / f".wikiepwing-doctor-{name}-{os.getpid()}"
    try:
        with probe.open("x", encoding="utf-8") as file:
            file.write("doctor probe\n")
    except OSError as error:
        return False, f"not writable ({error.strerror or error})"
    else:
        probe.unlink()
        return True, "writable"


def _free_disk_check(config: AppConfig) -> CheckResult:
    resources = config.section("resources")
    minimum_gib = cast(int, resources["minimum_free_disk_gib"])
    required_bytes = minimum_gib * 1024**3
    if not config.paths.work.is_dir():
        return CheckResult(
            "free_disk",
            "storage",
            "fail",
            True,
            f"work directory does not exist: {config.paths.work}",
            {"path": str(config.paths.work), "required_bytes": required_bytes},
        )
    free_bytes = shutil.disk_usage(config.paths.work).free
    return CheckResult(
        "free_disk",
        "storage",
        "pass" if free_bytes >= required_bytes else "fail",
        True,
        f"free={free_bytes} required={required_bytes}",
        {
            "path": str(config.paths.work),
            "free_bytes": free_bytes,
            "required_bytes": required_bytes,
        },
    )


def _tool_check(tool: ToolSpec) -> CheckResult:
    path = shutil.which(tool.name)
    if path is not None:
        return CheckResult(
            f"tool:{tool.name}",
            "tool",
            "pass",
            tool.required,
            path,
            {"path": path, "available": True},
        )
    return CheckResult(
        f"tool:{tool.name}",
        "tool",
        "fail" if tool.required else "warning",
        tool.required,
        "not found on PATH",
        {"path": None, "available": False},
    )


def render_doctor_text(report: DoctorReport) -> str:
    """Render a concise human-readable report."""
    lines = [f"Doctor: {'OK' if report.ok else 'FAILED'}"]
    for check in report.checks:
        display_name = check.name.removeprefix(f"{check.category}:")
        lines.append(f"[{check.status.upper()}] {check.category}/{display_name}: {check.detail}")
    return "\n".join(lines) + "\n"
