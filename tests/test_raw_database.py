from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from wikiepwing.ingest.database import (
    RawDatabaseError,
    connect_raw_database,
    initialize_raw_database,
)

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "raw"
EXPECTED_TABLES = {
    "article_licenses",
    "articles",
    "categories",
    "diagnostics",
    "ingest_duplicates",
    "licenses",
    "main_images",
    "metadata",
    "redirects",
    "schema_migrations",
    "templates",
}


def test_reports_integrity_check_start_and_completion(tmp_path: Path) -> None:
    reports: list[tuple[int, bool]] = []

    initialize_raw_database(
        tmp_path / "raw.sqlite3",
        MIGRATIONS,
        on_integrity_progress=lambda steps, complete: reports.append((steps, complete)),
    )

    assert reports[0] == (0, False)
    assert reports[-1][1] is True


def test_initial_migration_creates_strict_raw_schema(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)

    with connect_raw_database(database) as connection:
        tables = connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type = 'table' ORDER BY name"
        ).fetchall()
        assert {row["name"] for row in tables} == EXPECTED_TABLES
        assert all(" STRICT" in row["sql"].upper() for row in tables)
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert connection.execute("PRAGMA application_id").fetchone()[0] == 1380013892
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        migrations = connection.execute(
            "SELECT version, name, sha256 FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert [(row["version"], row["name"]) for row in migrations] == [(1, "initial")]
        assert all(len(row["sha256"]) == 64 for row in migrations)


def test_app_image_includes_raw_migrations() -> None:
    dockerfile = (Path(__file__).parents[1] / "docker" / "app.Dockerfile").read_text(
        encoding="utf-8"
    )

    assert "COPY migrations ./migrations" in dockerfile


def test_raw_schema_constraints_reject_inconsistent_rows(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)

    with connect_raw_database(database) as connection:
        connection.execute(
            """
            INSERT INTO articles (
                page_id, revision_id, title, normalized_title, namespace_id, url,
                date_modified, source_hash, source_sequence, ingest_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                100,
                "Emacs",
                "Emacs",
                0,
                "https://ja.wikipedia.org/wiki/Emacs",
                "2026-06-01T00:00:00Z",
                "a" * 64,
                0,
                "accepted",
            ),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO redirects (
                    target_page_id, redirect_title, normalized_redirect_title, ordinal
                ) VALUES (?, ?, ?, ?)
                """,
                (999, "GNU Emacs", "GNU Emacs", 0),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO articles (
                    page_id, revision_id, title, normalized_title, namespace_id, url,
                    date_modified, source_hash, source_sequence, ingest_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    2,
                    101,
                    "Linux",
                    "Linux",
                    0,
                    "https://ja.wikipedia.org/wiki/Linux",
                    "2026-06-01T00:00:00Z",
                    "b" * 64,
                    0,
                    "unknown_status",
                ),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO diagnostics (code, severity, stage, message, details_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("BAD", "ignored", "ingest", "invalid severity", "{}"),
            )


def test_migrations_are_idempotent_and_detect_changed_history(tmp_path: Path) -> None:
    database = tmp_path / "raw.sqlite3"
    initialize_raw_database(database, MIGRATIONS)
    initialize_raw_database(database, MIGRATIONS)
    copied = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, copied)
    migration = copied / "001_initial.sql"
    migration.write_text(migration.read_text(encoding="utf-8") + "\n-- changed\n", encoding="utf-8")

    with pytest.raises(RawDatabaseError, match="checksum mismatch"):
        initialize_raw_database(database, copied)


def test_failed_migration_is_rolled_back_without_partial_schema(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, migrations)
    (migrations / "002_broken.sql").write_text(
        "CREATE TABLE partial_table (id INTEGER PRIMARY KEY) STRICT;\nTHIS IS NOT SQL;\n",
        encoding="utf-8",
    )
    database = tmp_path / "raw.sqlite3"

    with pytest.raises(RawDatabaseError, match="migration 002 failed"):
        initialize_raw_database(database, migrations)

    with connect_raw_database(database) as connection:
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

    with pytest.raises(RawDatabaseError, match=message):
        initialize_raw_database(tmp_path / "raw.sqlite3", migrations, max_migration_bytes=64)
