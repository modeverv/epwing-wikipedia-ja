"""Validated fixed-query configuration for reference measurements."""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

MAX_QUERY_SET_BYTES = 64 * 1024
MAX_QUERY_BYTES = 4096
MAX_QUERY_COUNT = 1000
_ROOT_KEYS = {
    "schema_version",
    "identifier",
    "search_modes",
    "max_results_per_query",
    "queries",
}
_QUERY_KEYS = {"key", "text", "expected_presence"}
_SEARCH_MODES = {"word", "endword", "keyword", "cross", "exact"}
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")
_QUERY_KEY = re.compile(r"^[a-z][a-z0-9_]{0,99}$")


class QuerySetError(ValueError):
    """Raised when a fixed reference query set is unsafe or invalid."""


@dataclass(frozen=True, slots=True)
class FixedQuery:
    """One ordered query and its baseline existence expectation."""

    ordinal: int
    key: str
    text: str
    expected_presence: bool


@dataclass(frozen=True, slots=True)
class QuerySet:
    """Immutable validated reference query-set configuration."""

    schema_version: int
    identifier: str
    search_modes: tuple[str, ...]
    max_results_per_query: int
    queries: tuple[FixedQuery, ...]
    source_path: Path
    sha256: str


def load_query_set(
    path: Path,
    *,
    max_bytes: int = MAX_QUERY_SET_BYTES,
    max_query_bytes: int = MAX_QUERY_BYTES,
) -> QuerySet:
    """Read and validate a fixed query set without following a symlink source."""
    if max_bytes < 1 or max_query_bytes < 1:
        raise QuerySetError("query-set safety limits must be positive")
    source = path.expanduser()
    try:
        status = source.lstat()
    except OSError as error:
        raise QuerySetError(f"cannot inspect query set: {source}: {error}") from error
    if source.is_symlink():
        raise QuerySetError(f"query set must not be a symlink: {source}")
    if not source.is_file():
        raise QuerySetError(f"query set must be a regular file: {source}")
    if status.st_size == 0 or status.st_size > max_bytes:
        raise QuerySetError(
            f"query-set size limit {max_bytes} violated by {source}: {status.st_size}"
        )
    content = source.read_bytes()
    try:
        document = cast(dict[str, object], tomllib.loads(content.decode("utf-8")))
    except UnicodeDecodeError as error:
        raise QuerySetError(f"query set must be valid UTF-8: {source}: {error}") from error
    except tomllib.TOMLDecodeError as error:
        raise QuerySetError(f"invalid query-set TOML: {source}: {error}") from error
    return _validate_document(
        document,
        source.resolve(strict=True),
        hashlib.sha256(content).hexdigest(),
        max_query_bytes,
    )


def _validate_document(
    document: dict[str, object], source: Path, sha256: str, max_query_bytes: int
) -> QuerySet:
    unknown = sorted(set(document) - _ROOT_KEYS)
    if unknown:
        raise QuerySetError(f"unknown key in query set: {unknown[0]}")
    version = document.get("schema_version")
    if type(version) is not int:
        raise QuerySetError("schema_version must be an integer")
    if version != 1:
        raise QuerySetError(f"unsupported query-set schema_version: {version}")
    identifier = document.get("identifier")
    if not isinstance(identifier, str) or _IDENTIFIER.fullmatch(identifier) is None:
        raise QuerySetError("identifier must be a lowercase hyphenated identifier")
    modes = _validate_modes(document.get("search_modes"))
    maximum = document.get("max_results_per_query")
    if type(maximum) is not int or not 1 <= maximum <= 1000:
        raise QuerySetError("max_results_per_query must be an integer from 1 to 1000")
    raw_queries = document.get("queries")
    if not isinstance(raw_queries, list) or not 1 <= len(raw_queries) <= MAX_QUERY_COUNT:
        raise QuerySetError(f"queries must contain between 1 and {MAX_QUERY_COUNT} tables")
    queries = _validate_queries(raw_queries, max_query_bytes)
    return QuerySet(
        schema_version=version,
        identifier=identifier,
        search_modes=modes,
        max_results_per_query=maximum,
        queries=queries,
        source_path=source,
        sha256=sha256,
    )


def _validate_modes(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise QuerySetError("search_modes must be a non-empty list of strings")
    modes = tuple(cast(list[str], value))
    if len(set(modes)) != len(modes):
        raise QuerySetError("search_modes must be unique")
    unsupported = sorted(set(modes) - _SEARCH_MODES)
    if unsupported:
        raise QuerySetError(f"unsupported search mode: {unsupported[0]}")
    return modes


def _validate_queries(value: list[object], max_query_bytes: int) -> tuple[FixedQuery, ...]:
    queries: list[FixedQuery] = []
    seen_keys: set[str] = set()
    seen_texts: set[str] = set()
    for ordinal, raw_query in enumerate(value):
        if not isinstance(raw_query, dict):
            raise QuerySetError(f"queries[{ordinal}] must be a TOML table")
        query = cast(dict[str, object], raw_query)
        unknown = sorted(set(query) - _QUERY_KEYS)
        if unknown:
            raise QuerySetError(f"unknown key in queries[{ordinal}]: {unknown[0]}")
        key = query.get("key")
        if not isinstance(key, str) or _QUERY_KEY.fullmatch(key) is None:
            raise QuerySetError(f"queries[{ordinal}].key must be a lowercase identifier")
        if key in seen_keys:
            raise QuerySetError(f"duplicate query key: {key}")
        text = query.get("text")
        if not isinstance(text, str) or not text or text != text.strip():
            raise QuerySetError(f"queries[{ordinal}].text must be non-empty and trimmed")
        if any(ord(character) < 32 or ord(character) == 127 for character in text):
            raise QuerySetError(f"queries[{ordinal}].text contains a control character")
        if len(text.encode("utf-8")) > max_query_bytes:
            raise QuerySetError(
                f"queries[{ordinal}].text exceeds UTF-8 byte limit {max_query_bytes}"
            )
        if text in seen_texts:
            raise QuerySetError(f"duplicate query text: {text}")
        expected = query.get("expected_presence")
        if type(expected) is not bool:
            raise QuerySetError(f"queries[{ordinal}].expected_presence must be a boolean")
        queries.append(FixedQuery(ordinal, key, text, expected))
        seen_keys.add(key)
        seen_texts.add(text)
    return tuple(queries)
