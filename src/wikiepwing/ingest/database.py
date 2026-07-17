"""Explicit SQLite migration and verification support for raw.sqlite3."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

BUSY_TIMEOUT_MILLISECONDS = 5000
INTEGRITY_PROGRESS_VM_STEPS = 100_000
MAX_MIGRATION_BYTES = 1024 * 1024
_MIGRATION_NAME = re.compile(r"^(?P<version>[0-9]{3})_(?P<name>[a-z][a-z0-9_]*)\.sql$")


class RawDatabaseError(ValueError):
    """Raised when raw schema migration or verification fails."""


@dataclass(frozen=True, slots=True)
class Migration:
    """One validated numbered SQL migration."""

    version: int
    name: str
    sha256: str
    sql: str


def connect_raw_database(path: Path) -> sqlite3.Connection:
    """Open a raw database with required safety pragmas enabled."""
    connection = sqlite3.connect(path, timeout=BUSY_TIMEOUT_MILLISECONDS / 1000)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MILLISECONDS}")
    return connection


def initialize_raw_database(
    path: Path,
    migrations_path: Path | None = None,
    *,
    max_migration_bytes: int = MAX_MIGRATION_BYTES,
    on_integrity_progress: Callable[[int, bool], None] | None = None,
) -> Path:
    """Apply validated pending migrations and verify the resulting database."""
    migrations = _load_migrations(
        migrations_path or _default_migrations_path(), max_migration_bytes
    )
    database = path.expanduser().resolve(strict=False)
    database.parent.mkdir(parents=True, exist_ok=True)
    with connect_raw_database(database) as connection:
        applied = _read_applied_migrations(connection)
        _verify_applied_history(applied, migrations)
        for migration in migrations[len(applied) :]:
            _apply_migration(connection, migration)
        _verify_database(connection, on_progress=on_integrity_progress)
    return database


def _default_migrations_path() -> Path:
    candidates = (Path.cwd() / "migrations/raw", Path("/app/migrations/raw"))
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise RawDatabaseError("raw migration directory was not found")


def _load_migrations(directory: Path, max_bytes: int) -> tuple[Migration, ...]:
    if max_bytes < 1:
        raise RawDatabaseError("max_migration_bytes must be positive")
    root = directory.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise RawDatabaseError(f"migration path must be a directory: {root}")
    migrations: list[Migration] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.suffix != ".sql":
            continue
        if path.is_symlink():
            raise RawDatabaseError(f"migration must not be a symlink: {path.name}")
        match = _MIGRATION_NAME.fullmatch(path.name)
        if match is None or not path.is_file():
            raise RawDatabaseError(f"invalid migration filename: {path.name}")
        size = path.stat().st_size
        if size == 0 or size > max_bytes:
            raise RawDatabaseError(
                f"migration size limit {max_bytes} violated by {path.name}: {size}"
            )
        content = path.read_bytes()
        try:
            sql = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise RawDatabaseError(
                f"migration must be valid UTF-8: {path.name}: {error}"
            ) from error
        migrations.append(
            Migration(
                version=int(match.group("version")),
                name=match.group("name"),
                sha256=hashlib.sha256(content).hexdigest(),
                sql=sql,
            )
        )
    if not migrations:
        raise RawDatabaseError(f"no raw migrations found in: {root}")
    versions = [migration.version for migration in migrations]
    expected = list(range(1, len(migrations) + 1))
    if versions != expected:
        raise RawDatabaseError(f"migration versions must be contiguous from 001: found {versions}")
    return tuple(migrations)


def _read_applied_migrations(connection: sqlite3.Connection) -> tuple[sqlite3.Row, ...]:
    exists = connection.execute(
        "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = 'schema_migrations'"
    ).fetchone()
    if exists is None:
        return ()
    return tuple(
        connection.execute(
            "SELECT version, name, sha256 FROM schema_migrations ORDER BY version"
        ).fetchall()
    )


def _verify_applied_history(
    applied: tuple[sqlite3.Row, ...], migrations: tuple[Migration, ...]
) -> None:
    if len(applied) > len(migrations):
        raise RawDatabaseError("database contains unknown raw migrations")
    for index, row in enumerate(applied):
        migration = migrations[index]
        if row["version"] != migration.version or row["name"] != migration.name:
            raise RawDatabaseError(f"migration history mismatch at version {migration.version:03d}")
        if row["sha256"] != migration.sha256:
            raise RawDatabaseError(
                f"migration checksum mismatch at version {migration.version:03d}"
            )


def _apply_migration(connection: sqlite3.Connection, migration: Migration) -> None:
    name = migration.name.replace("'", "''")
    sha256 = migration.sha256.replace("'", "''")
    transaction = f"""
BEGIN IMMEDIATE;
{migration.sql}
INSERT INTO schema_migrations (version, name, sha256)
VALUES ({migration.version}, '{name}', '{sha256}');
PRAGMA user_version = {migration.version};
COMMIT;
"""
    try:
        connection.executescript(transaction)
    except sqlite3.Error as error:
        if connection.in_transaction:
            connection.rollback()
        raise RawDatabaseError(f"migration {migration.version:03d} failed: {error}") from error


def _verify_database(
    connection: sqlite3.Connection,
    *,
    on_progress: Callable[[int, bool], None] | None = None,
) -> None:
    progress_calls = 0

    def report_progress() -> int:
        nonlocal progress_calls
        progress_calls += 1
        if on_progress is not None:
            on_progress(progress_calls * INTEGRITY_PROGRESS_VM_STEPS, False)
        return 0

    if on_progress is not None:
        connection.set_progress_handler(report_progress, INTEGRITY_PROGRESS_VM_STEPS)
    try:
        if on_progress is not None:
            on_progress(0, False)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
    finally:
        connection.set_progress_handler(None, 0)
    if on_progress is not None:
        on_progress(progress_calls * INTEGRITY_PROGRESS_VM_STEPS, True)
    if integrity is None or integrity[0] != "ok":
        detail = "no result" if integrity is None else str(integrity[0])
        raise RawDatabaseError(f"raw database integrity check failed: {detail}")
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise RawDatabaseError(
            f"raw database foreign key check found {len(foreign_key_errors)} errors"
        )
