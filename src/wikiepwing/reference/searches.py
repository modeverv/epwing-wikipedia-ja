"""Bounded EB search adapter and deterministic reference-result persistence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import selectors
import sqlite3
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from wikiepwing.reference.database import (
    connect_reference_database,
    initialize_reference_database,
)
from wikiepwing.reference.inventory import build_reference_inventory
from wikiepwing.reference.queries import load_query_set

MAX_ADAPTER_OUTPUT_BYTES = 8 * 1024 * 1024
DEFAULT_SEARCH_TIMEOUT_SECONDS = 30.0
_DIRECTORY = re.compile(r"^[A-Za-z0-9_]{1,8}$")


class ReferenceSearchError(ValueError):
    """Raised when a reference search cannot be executed or persisted safely."""


@dataclass(frozen=True, slots=True)
class SearchHit:
    """One ranked EB search hit with stable heading and text positions."""

    rank: int
    heading: str
    heading_page: int
    heading_offset: int
    text_page: int
    text_offset: int

    @property
    def entry_locator(self) -> str:
        """Return the stable EB text page/offset locator."""
        return f"{self.text_page}:{self.text_offset}"


@dataclass(frozen=True, slots=True)
class SubbookSearch:
    """Search results and boundedness metadata for one subbook."""

    subbook_code: int
    directory: str
    title: str
    returned_count: int
    truncated: bool
    hits: tuple[SearchHit, ...]


class SearchExecutor(Protocol):
    """Interface used by the persistence layer for one query and mode."""

    def search(
        self, root: Path, mode: str, query: str, max_results: int
    ) -> tuple[SubbookSearch, ...]: ...


class EbSearchAdapter:
    """Invoke the fixed EB C adapter with bounded process output and time."""

    def __init__(
        self,
        executable: Path,
        *,
        timeout_seconds: float = DEFAULT_SEARCH_TIMEOUT_SECONDS,
        max_output_bytes: int = MAX_ADAPTER_OUTPUT_BYTES,
    ) -> None:
        source = executable.expanduser()
        if source.is_symlink():
            raise ReferenceSearchError(f"EB search adapter must not be a symlink: {source}")
        self.executable = source.resolve(strict=True)
        if not self.executable.is_file():
            raise ReferenceSearchError(
                f"EB search adapter must be a regular non-symlink file: {self.executable}"
            )
        if timeout_seconds <= 0 or max_output_bytes < 1:
            raise ReferenceSearchError("adapter timeout and output limit must be positive")
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes

    def search(
        self, root: Path, mode: str, query: str, max_results: int
    ) -> tuple[SubbookSearch, ...]:
        """Run one validated search and parse its strict ASCII protocol."""
        _validate_search_request(root, mode, query, max_results)
        command = [
            str(self.executable),
            str(root),
            mode,
            query,
            str(max_results),
        ]
        stdout, stderr, return_code = _run_bounded(
            command, self.timeout_seconds, self.max_output_bytes
        )
        if return_code != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            raise ReferenceSearchError(
                f"EB search adapter exit code {return_code}: {detail[:4096]}"
            )
        return _parse_adapter_output(stdout)


def run_reference_searches(
    reference_root: Path,
    query_set_path: Path,
    database_path: Path,
    adapter: SearchExecutor,
    migrations_path: Path | None = None,
) -> Path:
    """Execute every fixed query/mode and atomically persist a verified database."""
    inventory = build_reference_inventory(reference_root)
    if len(inventory.subbook_candidates) != 1:
        raise ReferenceSearchError(
            "reference search currently requires exactly one HONMON subbook candidate"
        )
    catalogs = tuple(
        entry for entry in inventory.entries if Path(entry.path).name.casefold() == "catalogs"
    )
    if len(catalogs) != 1 or catalogs[0].kind != "file":
        raise ReferenceSearchError("reference search currently requires exactly one CATALOGS file")
    query_set = load_query_set(query_set_path)
    destination = database_path.expanduser().resolve(strict=False)
    if destination == inventory.root or inventory.root in destination.parents:
        raise ReferenceSearchError("reference database must be outside the reference root")
    destination.parent.mkdir(parents=True, exist_ok=True)

    inventory_bytes = (
        json.dumps(inventory.payload(), ensure_ascii=False, indent=2, sort_keys=True).encode(
            "utf-8"
        )
        + b"\n"
    )
    inventory_sha256 = hashlib.sha256(inventory_bytes).hexdigest()
    catalog_path = inventory.root / catalogs[0].path
    catalog_sha256 = hashlib.sha256(catalog_path.read_bytes()).hexdigest()
    source_fingerprint = hashlib.sha256(
        f"{catalog_sha256}:{inventory_sha256}".encode("ascii")
    ).hexdigest()

    with tempfile.TemporaryDirectory(
        dir=destination.parent, prefix=f".{destination.name}."
    ) as temporary_directory:
        temporary_database = Path(temporary_directory) / destination.name
        initialize_reference_database(temporary_database, migrations_path)
        _populate_search_database(
            temporary_database,
            inventory.root,
            catalogs[0].path,
            catalogs[0].size_bytes,
            source_fingerprint,
            inventory_sha256,
            query_set,
            adapter,
        )
        _verify_search_database(
            temporary_database, len(query_set.queries) * len(query_set.search_modes)
        )
        os.replace(temporary_database, destination)
    return destination


def _run_bounded(
    command: list[str], timeout_seconds: float, max_output_bytes: int
) -> tuple[bytes, bytes, int]:
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    if process.stdout is None or process.stderr is None:
        process.kill()
        process.wait()
        raise ReferenceSearchError("EB search adapter pipes were not created")
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + timeout_seconds
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                process.wait()
                raise ReferenceSearchError(
                    f"EB search adapter timed out after {timeout_seconds:g} seconds"
                )
            events = selector.select(remaining)
            if not events:
                continue
            for key, _ in events:
                chunk = os.read(key.fd, 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                stream = streams[str(key.data)]
                stream.extend(chunk)
                if len(stream) > max_output_bytes:
                    process.kill()
                    process.wait()
                    raise ReferenceSearchError(
                        f"EB search adapter output limit {max_output_bytes} exceeded"
                    )
        return_code = process.wait()
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
        if process.poll() is None:
            process.kill()
            process.wait()
    return bytes(streams["stdout"]), bytes(streams["stderr"]), return_code


def _validate_search_request(root: Path, mode: str, query: str, max_results: int) -> None:
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ReferenceSearchError(f"reference root must be an absolute real directory: {root}")
    if mode not in {"exact", "word", "endword", "keyword", "cross"}:
        raise ReferenceSearchError(f"unsupported reference search mode: {mode}")
    if not query or query != query.strip() or len(query.encode("utf-8")) > 4096:
        raise ReferenceSearchError("reference query must be trimmed and at most 4096 UTF-8 bytes")
    if any(ord(character) < 32 or ord(character) == 127 for character in query):
        raise ReferenceSearchError("reference query contains a control character")
    if not 1 <= max_results <= 1000:
        raise ReferenceSearchError("max_results must be from 1 to 1000")


def _parse_adapter_output(output: bytes) -> tuple[SubbookSearch, ...]:
    try:
        lines = output.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ReferenceSearchError(f"adapter output must be ASCII: {error}") from error
    if not lines or lines[0] != "WIKIEPWING_EB_SEARCH\t1\tJISX0208":
        raise ReferenceSearchError("adapter output has an invalid header")
    builders: dict[int, tuple[str, str, int, bool, list[SearchHit]]] = {}
    for line_number, line in enumerate(lines[1:], start=2):
        fields = line.split("\t")
        try:
            if fields[0] == "S" and len(fields) == 6:
                code = int(fields[1])
                directory = fields[2]
                if code in builders or _DIRECTORY.fullmatch(directory) is None:
                    raise ValueError("invalid or duplicate subbook")
                title = bytes.fromhex(fields[3]).decode("euc_jp")
                returned_count = int(fields[4])
                truncated = _parse_protocol_boolean(fields[5])
                if code < 0 or returned_count < 0 or not title:
                    raise ValueError("invalid subbook metadata")
                builders[code] = (directory, title, returned_count, truncated, [])
            elif fields[0] == "R" and len(fields) == 8:
                code = int(fields[1])
                if code not in builders:
                    raise ValueError("result appears before its subbook")
                hit = SearchHit(
                    rank=int(fields[2]),
                    heading=bytes.fromhex(fields[3]).decode("euc_jp"),
                    heading_page=int(fields[4]),
                    heading_offset=int(fields[5]),
                    text_page=int(fields[6]),
                    text_offset=int(fields[7]),
                )
                if (
                    hit.rank != len(builders[code][4]) + 1
                    or not hit.heading
                    or hit.heading_page < 1
                    or hit.text_page < 1
                    or not 0 <= hit.heading_offset < 2048
                    or not 0 <= hit.text_offset < 2048
                ):
                    raise ValueError("invalid result fields")
                builders[code][4].append(hit)
            else:
                raise ValueError("unknown record")
        except (UnicodeDecodeError, ValueError) as error:
            raise ReferenceSearchError(
                f"invalid adapter record at line {line_number}: {error}"
            ) from error
    if not builders:
        raise ReferenceSearchError("adapter returned no subbooks")
    results: list[SubbookSearch] = []
    for code, (directory, title, returned_count, truncated, hits) in sorted(builders.items()):
        if returned_count != len(hits):
            raise ReferenceSearchError(
                f"adapter result count mismatch for subbook {directory}: {returned_count}"
            )
        results.append(
            SubbookSearch(code, directory, title, returned_count, truncated, tuple(hits))
        )
    return tuple(results)


def _parse_protocol_boolean(value: str) -> bool:
    if value == "0":
        return False
    if value == "1":
        return True
    raise ValueError("invalid boolean")


def _populate_search_database(
    database: Path,
    root: Path,
    catalog_path: str,
    catalog_size_bytes: int | None,
    source_fingerprint: str,
    inventory_sha256: str,
    query_set: object,
    adapter: SearchExecutor,
) -> None:
    from wikiepwing.reference.queries import QuerySet

    if not isinstance(query_set, QuerySet) or catalog_size_bytes is None:
        raise ReferenceSearchError("invalid validated reference metadata")
    with connect_reference_database(database) as connection:
        book_cursor = connection.execute(
            """
            INSERT INTO reference_books (
                source_fingerprint, catalog_path, catalog_size_bytes, inventory_sha256, identifier
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                source_fingerprint,
                catalog_path,
                catalog_size_bytes,
                inventory_sha256,
                query_set.identifier,
            ),
        )
        book_id = _require_last_row_id(book_cursor, "reference book")
        expected_subbooks: tuple[tuple[int, str, str], ...] | None = None
        subbook_ids: dict[int, int] = {}
        for query in query_set.queries:
            for mode_index, mode in enumerate(query_set.search_modes):
                searches = adapter.search(root, mode, query.text, query_set.max_results_per_query)
                metadata = tuple(
                    (search.subbook_code, search.directory, search.title) for search in searches
                )
                if expected_subbooks is None:
                    expected_subbooks = metadata
                    for code, directory, title in metadata:
                        cursor = connection.execute(
                            """
                            INSERT INTO reference_subbooks (book_id, code, title, directory)
                            VALUES (?, ?, ?, ?)
                            """,
                            (book_id, directory.upper(), title, directory),
                        )
                        subbook_ids[code] = _require_last_row_id(cursor, "reference subbook")
                elif metadata != expected_subbooks:
                    raise ReferenceSearchError("adapter subbook metadata changed between searches")
                ordinal = query.ordinal * len(query_set.search_modes) + mode_index
                cursor = connection.execute(
                    """
                    INSERT INTO reference_queries (
                        query_key, query_text, search_mode, ordinal, expected_presence
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        f"{query.key}:{mode}",
                        query.text,
                        mode,
                        ordinal,
                        int(query.expected_presence),
                    ),
                )
                query_id = _require_last_row_id(cursor, "reference query")
                has_results = False
                for search in searches:
                    subbook_id = subbook_ids[search.subbook_code]
                    for hit in search.hits:
                        has_results = True
                        connection.execute(
                            """
                            INSERT INTO reference_query_results (
                                query_id, subbook_id, rank, heading, entry_locator
                            ) VALUES (?, ?, ?, ?, ?)
                            """,
                            (query_id, subbook_id, hit.rank, hit.heading, hit.entry_locator),
                        )
                    if search.truncated:
                        _insert_diagnostic(
                            connection,
                            book_id,
                            subbook_id,
                            "warning",
                            "REF_QUERY_RESULTS_TRUNCATED",
                            f"query {query.key}:{mode} reached its result limit",
                            {"mode": mode, "query_key": query.key},
                        )
                if has_results != query.expected_presence:
                    _insert_diagnostic(
                        connection,
                        book_id,
                        None,
                        "warning",
                        "REF_QUERY_EXPECTATION_MISMATCH",
                        f"query {query.key}:{mode} presence differed from its fixed expectation",
                        {
                            "actual_presence": has_results,
                            "expected_presence": query.expected_presence,
                            "mode": mode,
                            "query_key": query.key,
                        },
                    )


def _insert_diagnostic(
    connection: sqlite3.Connection,
    book_id: int,
    subbook_id: int | None,
    severity: str,
    code: str,
    message: str,
    details: dict[str, object],
) -> None:
    connection.execute(
        """
        INSERT INTO reference_diagnostics (
            book_id, subbook_id, severity, code, message, details_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            book_id,
            subbook_id,
            severity,
            code,
            message,
            json.dumps(details, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        ),
    )


def _require_last_row_id(cursor: sqlite3.Cursor, label: str) -> int:
    value = cursor.lastrowid
    if value is None:
        raise ReferenceSearchError(f"failed to allocate {label} ID")
    return value


def _verify_search_database(database: Path, expected_query_count: int) -> None:
    with connect_reference_database(database) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise ReferenceSearchError("reference search database failed integrity_check")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise ReferenceSearchError("reference search database failed foreign_key_check")
        query_count = connection.execute("SELECT COUNT(query_id) FROM reference_queries").fetchone()
        if query_count is None or query_count[0] != expected_query_count:
            raise ReferenceSearchError(
                f"reference search database has unexpected query count: {query_count}"
            )
