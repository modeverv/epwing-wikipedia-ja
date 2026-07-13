"""Bounded reference entry reading and idempotent sample persistence."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from wikiepwing.reference.database import connect_reference_database
from wikiepwing.reference.searches import _run_bounded

MAX_BODY_BYTES = 256 * 1024
MAX_ADAPTER_OUTPUT_BYTES = 8 * 1024 * 1024
DEFAULT_ENTRY_TIMEOUT_SECONDS = 30.0
_DIRECTORY = re.compile(r"^[A-Za-z0-9_]{1,8}$")


class ReferenceEntryError(ValueError):
    """Raised when reference entry extraction or persistence is invalid."""


@dataclass(frozen=True, slots=True)
class EntrySample:
    """Bounded decoded entry text and observable EB hook counts."""

    text: str
    truncated: bool
    reference_count: int
    image_count: int
    narrow_gaiji_count: int
    wide_gaiji_count: int


class EntryExecutor(Protocol):
    """Interface used to read one entry by subbook directory and EB text locator."""

    def read(
        self,
        root: Path,
        subbook_directory: str,
        page: int,
        offset: int,
        max_bytes: int,
    ) -> EntrySample: ...


class EbEntryAdapter:
    """Invoke the EB entry C adapter with bounded process output and time."""

    def __init__(
        self,
        executable: Path,
        *,
        timeout_seconds: float = DEFAULT_ENTRY_TIMEOUT_SECONDS,
        max_output_bytes: int = MAX_ADAPTER_OUTPUT_BYTES,
    ) -> None:
        source = executable.expanduser()
        if source.is_symlink():
            raise ReferenceEntryError(f"EB entry adapter must not be a symlink: {source}")
        self.executable = source.resolve(strict=True)
        if not self.executable.is_file():
            raise ReferenceEntryError(f"EB entry adapter must be a regular file: {self.executable}")
        if timeout_seconds <= 0 or max_output_bytes < 1:
            raise ReferenceEntryError("adapter timeout and output limit must be positive")
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes

    def read(
        self,
        root: Path,
        subbook_directory: str,
        page: int,
        offset: int,
        max_bytes: int,
    ) -> EntrySample:
        """Read one entry and parse the strict ASCII adapter protocol."""
        _validate_request(root, subbook_directory, page, offset, max_bytes)
        stdout, stderr, return_code = _run_bounded(
            [
                str(self.executable),
                str(root),
                subbook_directory,
                str(page),
                str(offset),
                str(max_bytes),
            ],
            self.timeout_seconds,
            self.max_output_bytes,
        )
        if return_code != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            raise ReferenceEntryError(
                f"EB entry adapter exit code {return_code} at {page}:{offset}: {detail[:4096]}"
            )
        return _parse_output(stdout, subbook_directory, page, offset)


def sample_reference_entries(
    database_path: Path,
    reference_root: Path,
    adapter: EntryExecutor,
    *,
    max_body_bytes: int = MAX_BODY_BYTES,
) -> Path:
    """Read unique rank-one locators and idempotently store entry observations."""
    source_database = database_path.expanduser()
    if source_database.is_symlink():
        raise ReferenceEntryError(f"reference database must not be a symlink: {source_database}")
    database = source_database.resolve(strict=True)
    if not database.is_file():
        raise ReferenceEntryError(f"reference database must be a real file: {database}")
    root = reference_root.expanduser()
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ReferenceEntryError(f"reference root must be an absolute real directory: {root}")
    if not 1 <= max_body_bytes <= MAX_BODY_BYTES:
        raise ReferenceEntryError(f"max_body_bytes must be from 1 to {MAX_BODY_BYTES}")

    book_id, targets = _load_sample_targets(database)
    desired_entries: list[tuple[object, ...]] = []
    desired_diagnostics: list[tuple[object, ...]] = []
    for subbook_id, directory, title, locator in targets:
        page, offset = _parse_locator(locator)
        try:
            sample = adapter.read(root, directory, page, offset, max_body_bytes)
        except ReferenceEntryError as error:
            desired_diagnostics.append(
                _diagnostic_row(
                    book_id,
                    subbook_id,
                    "warning",
                    "REF_ENTRY_READ_FAILED",
                    f"entry sample at {locator} could not be read",
                    {"entry_locator": locator, "error": str(error)[:4096]},
                )
            )
            continue
        body = sample.text.encode("utf-8")
        desired_entries.append(
            (
                subbook_id,
                locator,
                title,
                sample.text[:1000],
                hashlib.sha256(body).hexdigest(),
                len(body),
                sample.reference_count,
                sample.image_count,
                sample.narrow_gaiji_count + sample.wide_gaiji_count,
            )
        )
        if sample.truncated:
            desired_diagnostics.append(
                _diagnostic_row(
                    book_id,
                    subbook_id,
                    "warning",
                    "REF_ENTRY_TEXT_TRUNCATED",
                    f"entry sample at {locator} reached the {max_body_bytes}-byte limit",
                    {"entry_locator": locator, "max_body_bytes": max_body_bytes},
                )
            )
    desired_diagnostics.append(
        _diagnostic_row(
            book_id,
            None,
            "info",
            "REF_MANUAL_VIEWER_RENDER_REQUIRED",
            "viewer rendering, layout, and visible media quality require manual review",
            {
                "automated_observations": [
                    "body_text",
                    "internal_reference_hooks",
                    "image_hooks",
                    "gaiji_hooks",
                ]
            },
        )
    )
    _store_samples_if_changed(database, desired_entries, desired_diagnostics)
    _verify_sample_database(database, len(desired_entries))
    return database


def _validate_request(root: Path, directory: str, page: int, offset: int, max_bytes: int) -> None:
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ReferenceEntryError(f"reference root must be an absolute real directory: {root}")
    if _DIRECTORY.fullmatch(directory) is None:
        raise ReferenceEntryError(f"invalid subbook directory: {directory}")
    if page < 1 or not 0 <= offset < 2048:
        raise ReferenceEntryError(f"invalid EB text position: {page}:{offset}")
    if not 1 <= max_bytes <= MAX_BODY_BYTES:
        raise ReferenceEntryError(f"max bytes must be from 1 to {MAX_BODY_BYTES}")


def _parse_output(output: bytes, directory: str, page: int, offset: int) -> EntrySample:
    try:
        lines = output.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ReferenceEntryError(f"adapter output must be ASCII: {error}") from error
    if len(lines) != 2 or lines[0] != "WIKIEPWING_EB_ENTRY\t1\tJISX0208":
        raise ReferenceEntryError("adapter entry output has an invalid header")
    fields = lines[1].split("\t")
    try:
        if (
            len(fields) != 10
            or fields[0] != "E"
            or fields[1] != directory
            or int(fields[2]) != page
            or int(fields[3]) != offset
        ):
            raise ValueError("position or directory mismatch")
        truncated = _protocol_boolean(fields[4])
        text = bytes.fromhex(fields[5]).decode("euc_jp")
        counts = tuple(int(field) for field in fields[6:10])
        if not text or any(count < 0 for count in counts):
            raise ValueError("empty text or negative hook count")
    except (UnicodeDecodeError, ValueError) as error:
        raise ReferenceEntryError(f"invalid adapter entry record: {error}") from error
    return EntrySample(text, truncated, counts[0], counts[1], counts[2], counts[3])


def _protocol_boolean(value: str) -> bool:
    if value == "0":
        return False
    if value == "1":
        return True
    raise ValueError("invalid boolean")


def _load_sample_targets(
    database: Path,
) -> tuple[int, tuple[tuple[int, str, str, str], ...]]:
    with connect_reference_database(database) as connection:
        books = connection.execute(
            "SELECT book_id FROM reference_books ORDER BY book_id"
        ).fetchall()
        if len(books) != 1:
            raise ReferenceEntryError("entry sampling requires exactly one reference book")
        rows = connection.execute(
            """
            SELECT s.subbook_id, s.directory, r.heading, r.entry_locator
            FROM reference_query_results AS r
            JOIN reference_queries AS q ON q.query_id = r.query_id
            JOIN reference_subbooks AS s ON s.subbook_id = r.subbook_id
            WHERE r.rank = 1
            ORDER BY q.ordinal, s.subbook_id, r.query_result_id
            """
        ).fetchall()
    seen: set[tuple[int, str]] = set()
    targets: list[tuple[int, str, str, str]] = []
    for row in rows:
        key = (row["subbook_id"], row["entry_locator"])
        if key in seen:
            continue
        seen.add(key)
        targets.append((row["subbook_id"], row["directory"], row["heading"], row["entry_locator"]))
    if not targets:
        raise ReferenceEntryError("reference database has no rank-one entries to sample")
    return books[0]["book_id"], tuple(targets)


def _parse_locator(locator: str) -> tuple[int, int]:
    parts = locator.split(":")
    if len(parts) != 2:
        raise ReferenceEntryError(f"invalid stored entry locator: {locator}")
    try:
        page, offset = (int(part) for part in parts)
    except ValueError as error:
        raise ReferenceEntryError(f"invalid stored entry locator: {locator}") from error
    if page < 1 or not 0 <= offset < 2048:
        raise ReferenceEntryError(f"invalid stored entry locator: {locator}")
    return page, offset


def _diagnostic_row(
    book_id: int,
    subbook_id: int | None,
    severity: str,
    code: str,
    message: str,
    details: dict[str, object],
) -> tuple[object, ...]:
    return (
        book_id,
        subbook_id,
        severity,
        code,
        message,
        json.dumps(details, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
    )


def _store_samples_if_changed(
    database: Path,
    entries: list[tuple[object, ...]],
    diagnostics: list[tuple[object, ...]],
) -> None:
    with connect_reference_database(database) as connection:
        existing_entries = [
            tuple(row)
            for row in connection.execute(
                """
                SELECT subbook_id, entry_locator, title, body_excerpt, body_sha256,
                       body_byte_count, internal_link_count, image_count, gaiji_count
                FROM reference_entries
                ORDER BY entry_id
                """
            ).fetchall()
        ]
        existing_diagnostics = [
            tuple(row)
            for row in connection.execute(
                """
                SELECT book_id, subbook_id, severity, code, message, details_json
                FROM reference_diagnostics
                WHERE code LIKE 'REF_ENTRY_%' OR code LIKE 'REF_MANUAL_%'
                ORDER BY diagnostic_id
                """
            ).fetchall()
        ]
        if existing_entries == entries and existing_diagnostics == diagnostics:
            return
        connection.execute("DELETE FROM reference_entries")
        connection.execute(
            """
            DELETE FROM reference_diagnostics
            WHERE code LIKE 'REF_ENTRY_%' OR code LIKE 'REF_MANUAL_%'
            """
        )
        connection.executemany(
            """
            INSERT INTO reference_entries (
                subbook_id, entry_locator, title, body_excerpt, body_sha256,
                body_byte_count, internal_link_count, image_count, gaiji_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            entries,
        )
        connection.executemany(
            """
            INSERT INTO reference_diagnostics (
                book_id, subbook_id, severity, code, message, details_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            diagnostics,
        )


def _verify_sample_database(database: Path, expected_entries: int) -> None:
    with connect_reference_database(database) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise ReferenceEntryError("sampled reference database failed integrity_check")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise ReferenceEntryError("sampled reference database failed foreign_key_check")
        count = connection.execute("SELECT COUNT(entry_id) FROM reference_entries").fetchone()
        if count is None or count[0] != expected_entries:
            raise ReferenceEntryError(
                f"sampled reference database has unexpected entry count: {count}"
            )
