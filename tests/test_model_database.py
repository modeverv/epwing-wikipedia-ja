from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from wikiepwing.model.database import (
    ModelDatabaseError,
    connect_model_database,
    initialize_model_database,
)

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "model"
EXPECTED_TABLES = {
    "articles",
    "diagnostics",
    "links",
    "media_references",
    "metadata",
    "schema_migrations",
}


def test_initial_migration_creates_strict_model_schema(tmp_path: Path) -> None:
    database = initialize_model_database(tmp_path / "model.sqlite3", MIGRATIONS)

    with connect_model_database(database) as connection:
        tables = connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type = 'table' ORDER BY name"
        ).fetchall()
        assert {row["name"] for row in tables} == EXPECTED_TABLES
        assert all(" STRICT" in row["sql"].upper() for row in tables)
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert connection.execute("PRAGMA application_id").fetchone()[0] == 1297040460
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        migrations = connection.execute(
            "SELECT version, name, sha256 FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert [(row["version"], row["name"]) for row in migrations] == [(1, "initial")]
        assert all(len(row["sha256"]) == 64 for row in migrations)


def test_model_schema_constraints_reject_inconsistent_rows(tmp_path: Path) -> None:
    database = initialize_model_database(tmp_path / "model.sqlite3", MIGRATIONS)

    with connect_model_database(database) as connection:
        connection.execute(
            """
            INSERT INTO articles (
                page_id, revision_id, title, normalized_title, source_url,
                source_date_modified, article_json_zstd, article_logical_hash,
                normalize_status, block_count, diagnostic_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                100,
                "Emacs",
                "Emacs",
                "https://ja.wikipedia.org/wiki/Emacs",
                "2026-06-01T00:00:00Z",
                b"\x00",
                "a" * 64,
                "complete",
                0,
                0,
            ),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO links (source_page_id, ordinal, target_title, resolution)
                VALUES (?, ?, ?, ?)
                """,
                (999, 0, "Ghost", "missing"),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO articles (
                    page_id, revision_id, title, normalized_title, source_url,
                    source_date_modified, article_json_zstd, article_logical_hash,
                    normalize_status, block_count, diagnostic_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    2,
                    101,
                    "Linux",
                    "Linux",
                    "https://ja.wikipedia.org/wiki/Linux",
                    "2026-06-01T00:00:00Z",
                    b"\x00",
                    "b" * 64,
                    "unknown_status",
                    0,
                    0,
                ),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO diagnostics (code, severity, stage, message, details_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("BAD", "ignored", "normalize", "invalid severity", "{}"),
            )


def test_model_migrations_are_idempotent_and_detect_changed_history(tmp_path: Path) -> None:
    database = tmp_path / "model.sqlite3"
    initialize_model_database(database, MIGRATIONS)
    initialize_model_database(database, MIGRATIONS)
    copied = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, copied)
    migration = copied / "001_initial.sql"
    migration.write_text(migration.read_text(encoding="utf-8") + "\n-- changed\n", encoding="utf-8")

    with pytest.raises(ModelDatabaseError, match="checksum mismatch"):
        initialize_model_database(database, copied)


def test_failed_model_migration_is_rolled_back_without_partial_schema(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, migrations)
    (migrations / "002_broken.sql").write_text(
        "CREATE TABLE partial_table (id INTEGER PRIMARY KEY) STRICT;\nTHIS IS NOT SQL;\n",
        encoding="utf-8",
    )
    database = tmp_path / "model.sqlite3"

    with pytest.raises(ModelDatabaseError, match="migration 002 failed"):
        initialize_model_database(database, migrations)

    with connect_model_database(database) as connection:
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
def test_invalid_model_migration_sets_are_rejected(tmp_path: Path, invalid_kind: str) -> None:
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

    with pytest.raises(ModelDatabaseError, match=message):
        initialize_model_database(tmp_path / "model.sqlite3", migrations, max_migration_bytes=64)
