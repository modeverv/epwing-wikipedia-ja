"""Validated, explicit configuration loading for the build pipeline."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when a configuration file is invalid or unsupported."""


@dataclass(frozen=True, slots=True)
class PathsConfig:
    data_dir: Path
    output_dir: Path
    reports_dir: Path


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    log_level: str


@dataclass(frozen=True, slots=True)
class BuildConfig:
    schema_version: int
    project: str
    profile: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    build: BuildConfig
    paths: PathsConfig
    runtime: RuntimeConfig


def _require_table(document: dict[str, Any], key: str) -> dict[str, Any]:
    value = document.get(key)
    if not isinstance(value, dict):
        raise ConfigurationError(f"[{key}] must be a TOML table")
    return value


def _validate_keys(table: dict[str, Any], allowed: set[str], name: str) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise ConfigurationError(f"unsupported keys in [{name}]: {', '.join(unknown)}")


def _require_string(table: dict[str, Any], key: str, name: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"[{name}].{key} must be a non-empty string")
    return value


def load_config(path: Path) -> AppConfig:
    """Load the Phase 0 configuration and reject unknown semantic keys."""
    try:
        with path.open("rb") as file:
            document = tomllib.load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(f"configuration file does not exist: {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(f"invalid TOML in {path}: {error}") from error

    _validate_keys(document, {"build", "paths", "runtime"}, "root")
    build = _require_table(document, "build")
    paths = _require_table(document, "paths")
    runtime = _require_table(document, "runtime")
    _validate_keys(build, {"schema_version", "project", "profile"}, "build")
    _validate_keys(paths, {"data_dir", "output_dir", "reports_dir"}, "paths")
    _validate_keys(runtime, {"log_level"}, "runtime")

    version = build.get("schema_version")
    if version != 1:
        raise ConfigurationError("[build].schema_version must be 1")
    log_level = _require_string(runtime, "log_level", "runtime").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError("[runtime].log_level is not a supported logging level")

    return AppConfig(
        build=BuildConfig(
            version,
            _require_string(build, "project", "build"),
            _require_string(build, "profile", "build"),
        ),
        paths=PathsConfig(
            Path(_require_string(paths, "data_dir", "paths")),
            Path(_require_string(paths, "output_dir", "paths")),
            Path(_require_string(paths, "reports_dir", "paths")),
        ),
        runtime=RuntimeConfig(log_level),
    )
