from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from wikiepwing.gaiji.database import (
    GaijiDatabaseError,
    connect_gaiji_database,
    initialize_gaiji_database,
)

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "gaiji"
EXPECTED_TABLES = {"gaiji_registry", "schema_migrations"}


def test_initial_migration_creates_strict_gaiji_schema(tmp_path: Path) -> None:
    database = initialize_gaiji_database(tmp_path / "gaiji.sqlite3", MIGRATIONS)

    with connect_gaiji_database(database) as connection:
        tables = connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type = 'table' ORDER BY name"
        ).fetchall()
        assert {row["name"] for row in tables} == EXPECTED_TABLES
        assert all(" STRICT" in row["sql"].upper() for row in tables)
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert connection.execute("PRAGMA application_id").fetchone()[0] == 1195461193
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        migrations = connection.execute(
            "SELECT version, name, sha256 FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert [(row["version"], row["name"]) for row in migrations] == [(1, "initial")]
        assert all(len(row["sha256"]) == 64 for row in migrations)


def test_gaiji_registry_accepts_a_valid_row(tmp_path: Path) -> None:
    database = initialize_gaiji_database(tmp_path / "gaiji.sqlite3", MIGRATIONS)

    with connect_gaiji_database(database) as connection:
        connection.execute(
            """
            INSERT INTO gaiji_registry (
                unicode_sequence, normalized_sequence, width_class,
                font_source_identifier, bitmap_hash, assigned_gaiji_code, usage_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("\U00020000", "\U00020000", "full", "noto-cjk-1.0", "a" * 64, "F0A1", 1),
        )
        row = connection.execute("SELECT * FROM gaiji_registry").fetchone()
        assert row["width_class"] == "full"
        assert row["usage_count"] == 1


def test_gaiji_registry_rejects_duplicate_normalized_sequence(tmp_path: Path) -> None:
    database = initialize_gaiji_database(tmp_path / "gaiji.sqlite3", MIGRATIONS)

    with connect_gaiji_database(database) as connection:
        connection.execute(
            """
            INSERT INTO gaiji_registry (
                unicode_sequence, normalized_sequence, width_class, font_source_identifier
            ) VALUES (?, ?, ?, ?)
            """,
            ("\U00020000", "\U00020000", "full", "noto-cjk-1.0"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO gaiji_registry (
                    unicode_sequence, normalized_sequence, width_class, font_source_identifier
                ) VALUES (?, ?, ?, ?)
                """,
                ("\U00020000", "\U00020000", "half", "noto-cjk-1.0"),
            )


def test_gaiji_registry_rejects_invalid_width_class(tmp_path: Path) -> None:
    database = initialize_gaiji_database(tmp_path / "gaiji.sqlite3", MIGRATIONS)

    with connect_gaiji_database(database) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO gaiji_registry (
                    unicode_sequence, normalized_sequence, width_class, font_source_identifier
                ) VALUES (?, ?, ?, ?)
                """,
                ("\U00020000", "\U00020000", "wide", "noto-cjk-1.0"),
            )


def test_gaiji_registry_rejects_negative_usage_count(tmp_path: Path) -> None:
    database = initialize_gaiji_database(tmp_path / "gaiji.sqlite3", MIGRATIONS)

    with connect_gaiji_database(database) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO gaiji_registry (
                    unicode_sequence, normalized_sequence, width_class,
                    font_source_identifier, usage_count
                ) VALUES (?, ?, ?, ?, ?)
                """,
                ("\U00020000", "\U00020000", "full", "noto-cjk-1.0", -1),
            )


def test_gaiji_migrations_are_idempotent_and_detect_changed_history(tmp_path: Path) -> None:
    database = tmp_path / "gaiji.sqlite3"
    initialize_gaiji_database(database, MIGRATIONS)
    initialize_gaiji_database(database, MIGRATIONS)
    copied = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, copied)
    migration = copied / "001_initial.sql"
    migration.write_text(migration.read_text(encoding="utf-8") + "\n-- changed\n", encoding="utf-8")

    with pytest.raises(GaijiDatabaseError, match="checksum mismatch"):
        initialize_gaiji_database(database, copied)


def test_failed_gaiji_migration_is_rolled_back_without_partial_schema(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, migrations)
    (migrations / "002_broken.sql").write_text(
        "CREATE TABLE partial_table (id INTEGER PRIMARY KEY) STRICT;\nTHIS IS NOT SQL;\n",
        encoding="utf-8",
    )
    database = tmp_path / "gaiji.sqlite3"

    with pytest.raises(GaijiDatabaseError, match="migration 002 failed"):
        initialize_gaiji_database(database, migrations)

    with connect_gaiji_database(database) as connection:
        assert (
            connection.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = 'partial_table'"
            ).fetchone()
            is None
        )
        versions = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert [row["version"] for row in versions] == [1]


@pytest.mark.parametrize("invalid_kind", ["gap", "symlink", "oversized"])
def test_invalid_gaiji_migration_sets_are_rejected(tmp_path: Path, invalid_kind: str) -> None:
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

    with pytest.raises(GaijiDatabaseError, match=message):
        initialize_gaiji_database(tmp_path / "gaiji.sqlite3", migrations, max_migration_bytes=64)
