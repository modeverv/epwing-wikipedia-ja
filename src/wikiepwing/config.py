"""Validated TOML configuration loading and deterministic layer merging."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import cast


class ConfigurationError(ValueError):
    """Raised when configuration input is missing, malformed, or unsupported."""


@dataclass(frozen=True, slots=True)
class PathsConfig:
    """Resolved filesystem locations used by the pipeline."""

    sources: Path
    reference: Path
    work: Path
    cache: Path
    output: Path
    reports: Path
    logs: Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated application configuration with immutable merged values."""

    schema_version: int
    project: str
    profile: str
    paths: PathsConfig
    source_files: tuple[Path, ...]
    _values: Mapping[str, object]

    def section(self, name: str) -> Mapping[str, object]:
        """Return a named configuration table as a read-only mapping."""
        value = self._values.get(name)
        if not isinstance(value, Mapping):
            raise KeyError(f"configuration section does not exist: {name}")
        return cast(Mapping[str, object], value)


class _Kind(Enum):
    STRING = "a string"
    INTEGER = "an integer"
    FLOAT = "a float"
    BOOLEAN = "a boolean"
    STRING_LIST = "a list of strings"


type _SchemaNode = _Kind | dict[str, "_SchemaNode"]


_SCHEMA: dict[str, _SchemaNode] = {
    "schema_version": _Kind.INTEGER,
    "project": _Kind.STRING,
    "profile": _Kind.STRING,
    "paths": {
        "sources": _Kind.STRING,
        "reference": _Kind.STRING,
        "work": _Kind.STRING,
        "cache": _Kind.STRING,
        "output": _Kind.STRING,
        "reports": _Kind.STRING,
        "logs": _Kind.STRING,
    },
    "source": {
        "provider": _Kind.STRING,
        "namespace": _Kind.INTEGER,
        "snapshot": _Kind.STRING,
        "allow_xml_fallback": _Kind.BOOLEAN,
        "verify_sha256": _Kind.BOOLEAN,
        "enterprise": {
            "api_base": _Kind.STRING,
            "auth_base": _Kind.STRING,
            "request_timeout_seconds": _Kind.INTEGER,
            "download_timeout_seconds": _Kind.INTEGER,
            "max_retries": _Kind.INTEGER,
        },
        "xml": {
            "base_url": _Kind.STRING,
            "include_redirect_sql": _Kind.BOOLEAN,
            "include_page_sql": _Kind.BOOLEAN,
        },
    },
    "ingest": {
        "batch_size": _Kind.INTEGER,
        "max_title_bytes": _Kind.INTEGER,
        "max_url_bytes": _Kind.INTEGER,
        "max_html_bytes": _Kind.INTEGER,
        "max_wikitext_bytes": _Kind.INTEGER,
        "zstd_level": _Kind.INTEGER,
        "strict_required_fields": _Kind.BOOLEAN,
    },
    "normalize": {
        "workers": _Kind.INTEGER,
        "queue_depth": _Kind.INTEGER,
        "html_recover": _Kind.BOOLEAN,
        "preserve_unknown_text": _Kind.BOOLEAN,
        "max_dom_depth": _Kind.INTEGER,
        "remove_edit_ui": _Kind.BOOLEAN,
        "remove_navboxes": _Kind.BOOLEAN,
        "remove_authority_control": _Kind.BOOLEAN,
    },
    "text": {
        "internal_unicode_normalization": _Kind.STRING,
        "index_unicode_normalization": _Kind.STRING,
        "normalize_index_spaces": _Kind.BOOLEAN,
        "casefold_ascii": _Kind.BOOLEAN,
        "generate_hiragana_variant": _Kind.BOOLEAN,
        "generate_katakana_variant": _Kind.BOOLEAN,
        "remove_index_punctuation": _Kind.BOOLEAN,
    },
    "tables": {
        "enabled": _Kind.BOOLEAN,
        "simple_max_columns": _Kind.INTEGER,
        "simple_max_rows": _Kind.INTEGER,
        "wide_max_columns": _Kind.INTEGER,
        "max_rows": _Kind.INTEGER,
        "max_cells": _Kind.INTEGER,
        "oversized_action": _Kind.STRING,
    },
    "infobox": {
        "enabled": _Kind.BOOLEAN,
        "max_fields": _Kind.INTEGER,
        "remove_empty_fields": _Kind.BOOLEAN,
    },
    "references": {
        "enabled": _Kind.BOOLEAN,
        "max_references": _Kind.INTEGER,
        "external_urls": _Kind.STRING,
    },
    "images": {
        "enabled": _Kind.BOOLEAN,
        "max_per_article": _Kind.INTEGER,
        "preferred_width": _Kind.INTEGER,
        "max_download_bytes": _Kind.INTEGER,
        "max_pixels": _Kind.INTEGER,
        "allowed_hosts": _Kind.STRING_LIST,
        "allow_svg": _Kind.BOOLEAN,
        "allow_animated": _Kind.BOOLEAN,
        "missing_license_action": _Kind.STRING,
    },
    "math": {
        "enabled": _Kind.BOOLEAN,
        "render_graphics": _Kind.BOOLEAN,
        "max_source_bytes": _Kind.INTEGER,
        "render_timeout_seconds": _Kind.INTEGER,
    },
    "gaiji": {
        "enabled": _Kind.BOOLEAN,
        "font_family": _Kind.STRING,
        "font_package_id": _Kind.STRING,
        "fallback_format": _Kind.STRING,
    },
    "search": {
        "include_titles": _Kind.BOOLEAN,
        "include_redirects": _Kind.BOOLEAN,
        "include_aliases": _Kind.BOOLEAN,
        "include_categories": _Kind.BOOLEAN,
        "include_heading_keywords": _Kind.BOOLEAN,
        "include_infobox_keywords": _Kind.BOOLEAN,
        "max_terms_per_article": _Kind.INTEGER,
        "max_key_bytes": _Kind.INTEGER,
    },
    "epwing": {
        "backend": _Kind.STRING,
        "book_title": _Kind.STRING,
        "subbook_name": _Kind.STRING,
        "ebzip_level": _Kind.INTEGER,
        "entry_budget_bytes": _Kind.INTEGER,
        "archive_timestamp": _Kind.STRING,
    },
    "resources": {
        "worker_count": _Kind.INTEGER,
        "image_worker_count": _Kind.INTEGER,
        "math_worker_count": _Kind.INTEGER,
        "sqlite_cache_mib": _Kind.INTEGER,
        "minimum_free_disk_gib": _Kind.INTEGER,
    },
    "verification": {
        "random_sample_size": _Kind.INTEGER,
        "fixed_seed": _Kind.INTEGER,
        "fail_on_fatal": _Kind.BOOLEAN,
        "max_article_error_rate": _Kind.FLOAT,
    },
    "distribution": {
        "mode": _Kind.STRING,
        "include_attribution_appendix": _Kind.BOOLEAN,
        "exclude_images_without_license": _Kind.BOOLEAN,
    },
}


def _read_document(path: Path) -> dict[str, object]:
    source_path = path.expanduser().resolve()
    try:
        with source_path.open("rb") as file:
            document = cast(dict[str, object], tomllib.load(file))
    except OSError as error:
        raise ConfigurationError(
            f"cannot read configuration file {source_path}: {error}"
        ) from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(f"invalid TOML in {source_path}: {error}") from error

    _validate_table(document, _SCHEMA)
    version = document.get("schema_version")
    if version is not None and version != 1:
        raise ConfigurationError(f"unsupported schema_version: {version}")
    return _resolve_document_paths(document, source_path.parent)


def _validate_table(
    table: Mapping[str, object],
    schema: Mapping[str, _SchemaNode],
    prefix: str = "",
) -> None:
    unknown = sorted(set(table) - set(schema))
    if unknown:
        path = f"{prefix}.{unknown[0]}" if prefix else unknown[0]
        raise ConfigurationError(f"unknown configuration key: {path}")

    for key, value in table.items():
        path = f"{prefix}.{key}" if prefix else key
        node = schema[key]
        if isinstance(node, dict):
            if not isinstance(value, dict):
                raise ConfigurationError(f"{path} must be a TOML table")
            _validate_table(cast(dict[str, object], value), node, path)
        else:
            _validate_value(value, node, path)


def _validate_value(value: object, kind: _Kind, path: str) -> None:
    valid = False
    if kind is _Kind.STRING:
        valid = type(value) is str
    elif kind is _Kind.INTEGER:
        valid = type(value) is int
    elif kind is _Kind.FLOAT:
        valid = type(value) is float
    elif kind is _Kind.BOOLEAN:
        valid = type(value) is bool
    elif kind is _Kind.STRING_LIST:
        valid = isinstance(value, list) and all(type(item) is str for item in value)
    if not valid:
        raise ConfigurationError(f"{path} must be {kind.value}")


def _resolve_document_paths(document: dict[str, object], parent: Path) -> dict[str, object]:
    paths = document.get("paths")
    if not isinstance(paths, dict):
        return document

    resolved_document = dict(document)
    resolved_paths = dict(cast(dict[str, object], paths))
    for key, value in resolved_paths.items():
        path = Path(cast(str, value)).expanduser()
        resolved_paths[key] = path.resolve() if path.is_absolute() else (parent / path).resolve()
    resolved_document["paths"] = resolved_paths
    return resolved_document


def _deep_merge(base: dict[str, object], overlay: Mapping[str, object]) -> dict[str, object]:
    merged = dict(base)
    for key, value in overlay.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(
                cast(dict[str, object], existing),
                cast(dict[str, object], value),
            )
        else:
            merged[key] = value
    return merged


def _require_value(values: Mapping[str, object], key: str, expected: type[object]) -> object:
    value = values.get(key)
    if type(value) is not expected:
        raise ConfigurationError(f"required configuration value is missing or invalid: {key}")
    return value


def _require_paths(values: Mapping[str, object]) -> PathsConfig:
    raw_paths = values.get("paths")
    if not isinstance(raw_paths, Mapping):
        raise ConfigurationError("required configuration table is missing: paths")
    paths = cast(Mapping[str, object], raw_paths)

    def require_path(key: str) -> Path:
        value = paths.get(key)
        if not isinstance(value, Path):
            raise ConfigurationError(f"required configuration path is missing: paths.{key}")
        return value

    return PathsConfig(
        sources=require_path("sources"),
        reference=require_path("reference"),
        work=require_path("work"),
        cache=require_path("cache"),
        output=require_path("output"),
        reports=require_path("reports"),
        logs=require_path("logs"),
    )


def _validate_semantics(values: Mapping[str, object], paths: PathsConfig) -> None:
    _reject_negative_numbers(values)

    images = cast(Mapping[str, object], values["images"])
    if images["enabled"] is True and images["max_per_article"] == 0:
        raise ConfigurationError("images.max_per_article must be positive when images are enabled")

    distribution = cast(Mapping[str, object], values["distribution"])
    if distribution["mode"] == "public":
        if images["missing_license_action"] == "warn":
            raise ConfigurationError(
                "images.missing_license_action cannot be warn in public distribution mode"
            )
        if distribution["include_attribution_appendix"] is not True:
            raise ConfigurationError(
                "distribution.include_attribution_appendix must be true in public mode"
            )
        if distribution["exclude_images_without_license"] is not True:
            raise ConfigurationError(
                "distribution.exclude_images_without_license must be true in public mode"
            )

    if _is_within(paths.sources, paths.reference):
        raise ConfigurationError("paths.sources must not be inside paths.reference")
    if _is_within(paths.output, paths.reference):
        raise ConfigurationError("paths.output must not be inside paths.reference")


def _reject_negative_numbers(values: Mapping[str, object], prefix: str = "") -> None:
    for key, value in values.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, Mapping):
            _reject_negative_numbers(cast(Mapping[str, object], value), path)
        elif type(value) in {int, float} and cast(int | float, value) < 0:
            raise ConfigurationError(f"{path} must not be negative")


def _is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        table = cast(dict[str, object], value)
        return MappingProxyType({key: _freeze(item) for key, item in table.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in cast(list[object], value))
    return value


def load_config(
    default_path: Path,
    override_paths: Sequence[Path] = (),
) -> AppConfig:
    """Load, validate, and merge TOML files in order, with later values winning."""
    source_files = tuple(path.expanduser().resolve() for path in (default_path, *override_paths))
    merged = _read_document(source_files[0])
    for path in source_files[1:]:
        merged = _deep_merge(merged, _read_document(path))

    schema_version = cast(int, _require_value(merged, "schema_version", int))
    if schema_version != 1:
        raise ConfigurationError(f"unsupported schema_version: {schema_version}")
    project = cast(str, _require_value(merged, "project", str))
    profile = cast(str, _require_value(merged, "profile", str))
    paths = _require_paths(merged)
    _validate_semantics(merged, paths)
    frozen = cast(Mapping[str, object], _freeze(merged))
    return AppConfig(
        schema_version=schema_version,
        project=project,
        profile=profile,
        paths=paths,
        source_files=source_files,
        _values=frozen,
    )
