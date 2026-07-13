from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from wikiepwing.reference.database import (
    ReferenceDatabaseError,
    connect_reference_database,
    initialize_reference_database,
)

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "reference"
EXPECTED_TABLES = {
    "reference_books",
    "reference_diagnostics",
    "reference_entries",
    "reference_metrics",
    "reference_queries",
    "reference_query_results",
    "reference_subbooks",
    "schema_migrations",
}


def test_initial_migration_creates_strict_reference_schema(tmp_path: Path) -> None:
    database = initialize_reference_database(tmp_path / "reference.sqlite3", MIGRATIONS)

    with connect_reference_database(database) as connection:
        tables = connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type = 'table' ORDER BY name"
        ).fetchall()
        assert {row["name"] for row in tables} == EXPECTED_TABLES
        assert all(" STRICT" in row["sql"].upper() for row in tables)
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        migrations = connection.execute(
            "SELECT version, name, sha256 FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert [(row["version"], row["name"]) for row in migrations] == [
            (1, "initial"),
            (2, "allow_duplicate_query_locators"),
        ]
        assert all(len(row["sha256"]) == 64 for row in migrations)


def test_app_image_includes_reference_migrations() -> None:
    dockerfile = (Path(__file__).parents[1] / "docker" / "app.Dockerfile").read_text(
        encoding="utf-8"
    )

    assert "COPY migrations ./migrations" in dockerfile


def test_reference_schema_constraints_reject_inconsistent_rows(tmp_path: Path) -> None:
    database = initialize_reference_database(tmp_path / "reference.sqlite3", MIGRATIONS)

    with connect_reference_database(database) as connection:
        connection.execute(
            """
            INSERT INTO reference_books (
                source_fingerprint, catalog_path, catalog_size_bytes, inventory_sha256, identifier
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("a" * 64, "catalogs", 2048, "b" * 64, "boookends-2023"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO reference_subbooks (book_id, code, title, directory)
                VALUES (?, ?, ?, ?)
                """,
                (999, "WIKIP", "Wikipedia", "WIKIP"),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO reference_diagnostics (
                    book_id, subbook_id, severity, code, message, details_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (1, None, "ignored", "BAD", "invalid severity", "{}"),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO reference_metrics (
                    book_id, subbook_id, metric_name, integer_value, real_value, text_value, unit
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (1, None, "ambiguous", 1, 1.0, None, "count"),
            )


def test_migrations_are_idempotent_and_detect_changed_history(tmp_path: Path) -> None:
    database = tmp_path / "reference.sqlite3"
    initialize_reference_database(database, MIGRATIONS)
    initialize_reference_database(database, MIGRATIONS)
    copied = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, copied)
    migration = copied / "001_initial.sql"
    migration.write_text(migration.read_text(encoding="utf-8") + "\n-- changed\n", encoding="utf-8")

    with pytest.raises(ReferenceDatabaseError, match="checksum mismatch"):
        initialize_reference_database(database, copied)


def test_failed_migration_is_rolled_back_without_partial_schema(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, migrations)
    (migrations / "003_broken.sql").write_text(
        "CREATE TABLE partial_table (id INTEGER PRIMARY KEY) STRICT;\nTHIS IS NOT SQL;\n",
        encoding="utf-8",
    )
    database = tmp_path / "reference.sqlite3"

    with pytest.raises(ReferenceDatabaseError, match="migration 003 failed"):
        initialize_reference_database(database, migrations)

    with connect_reference_database(database) as connection:
        assert (
            connection.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = 'partial_table'"
            ).fetchone()
            is None
        )
        versions = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert [row["version"] for row in versions] == [1, 2]


@pytest.mark.parametrize("invalid_kind", ["gap", "symlink", "oversized"])
def test_invalid_migration_sets_are_rejected(tmp_path: Path, invalid_kind: str) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    first = migrations / "001_initial.sql"
    first.write_text("CREATE TABLE ok (id INTEGER PRIMARY KEY) STRICT;\n", encoding="utf-8")
    if invalid_kind == "gap":
        (migrations / "003_gap.sql").write_text("SELECT 1;\n", encoding="utf-8")
        message = "contiguous"
    elif invalid_kind == "symlink":
        (migrations / "002_link.sql").symlink_to(first)
        message = "symlink"
    else:
        (migrations / "002_large.sql").write_bytes(b"-" * 65)
        message = "size limit"

    with pytest.raises(ReferenceDatabaseError, match=message):
        initialize_reference_database(
            tmp_path / "reference.sqlite3", migrations, max_migration_bytes=64
        )
