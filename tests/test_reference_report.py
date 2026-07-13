from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from wikiepwing.reference.database import (
    connect_reference_database,
    initialize_reference_database,
)
from wikiepwing.reference.report import ReferenceReportError, write_reference_report

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "reference"


def _make_reference_database(tmp_path: Path) -> Path:
    database = initialize_reference_database(tmp_path / "reference.sqlite3", MIGRATIONS)
    with connect_reference_database(database) as connection:
        connection.execute(
            """
            INSERT INTO reference_books (
                source_fingerprint, catalog_path, catalog_size_bytes, inventory_sha256, identifier
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("a" * 64, "CATALOGS", 2048, "b" * 64, "Boookends 2023"),
        )
        connection.execute(
            """
            INSERT INTO reference_subbooks (book_id, code, title, directory)
            VALUES (1, 'WIKIP', '日本語<script>Wikipedia', 'wikip')
            """
        )
        connection.execute(
            """
            INSERT INTO reference_queries (
                query_key, query_text, search_mode, ordinal, expected_presence
            ) VALUES ('emacs:word', 'Emacs', 'word', 0, 1)
            """
        )
        connection.execute(
            """
            INSERT INTO reference_query_results (
                query_id, subbook_id, rank, heading, entry_locator
            ) VALUES (1, 1, 1, 'Emacs & editor', '30:40')
            """
        )
        connection.execute(
            """
            INSERT INTO reference_entries (
                subbook_id, entry_locator, title, body_excerpt, body_sha256,
                body_byte_count, internal_link_count, image_count, gaiji_count
            ) VALUES (1, '30:40', 'Emacs', '本文 <unsafe>', ?, 13, 3, 0, 2)
            """,
            (hashlib.sha256("本文 <unsafe>".encode()).hexdigest(),),
        )
        connection.executemany(
            """
            INSERT INTO reference_diagnostics (
                book_id, subbook_id, severity, code, message, details_json
            ) VALUES (1, ?, ?, ?, ?, ?)
            """,
            (
                (1, "warning", "REF_QUERY_RESULTS_TRUNCATED", "limited", '{"limit":100}'),
                (
                    None,
                    "info",
                    "REF_MANUAL_VIEWER_RENDER_REQUIRED",
                    "viewer review required",
                    "{}",
                ),
            ),
        )
    return database


def _hashes(paths: tuple[Path, Path, Path]) -> tuple[str, ...]:
    return tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths)


def test_reference_report_is_complete_escaped_and_deterministic(tmp_path: Path) -> None:
    database = _make_reference_database(tmp_path)
    output = tmp_path / "reports"

    paths = write_reference_report(database, output)
    first_hashes = _hashes(paths)
    second_paths = write_reference_report(database, output)

    assert paths == second_paths
    assert _hashes(second_paths) == first_hashes
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["summary"] == {
        "diagnostic_count": 2,
        "entry_count": 1,
        "query_count": 1,
        "query_result_count": 1,
        "subbook_count": 1,
    }
    assert payload["queries"][0]["results"][0]["heading"] == "Emacs & editor"
    assert payload["entries"][0]["gaiji_count"] == 2
    assert payload["diagnostics"][0]["details"] == {"limit": 100}
    html = paths[1].read_text(encoding="utf-8")
    assert "日本語&lt;script&gt;Wikipedia" in html
    assert "本文 &lt;unsafe&gt;" in html
    assert "<script" not in html.lower()
    checklist = paths[2].read_text(encoding="utf-8")
    assert "Viewer name/version" in checklist
    assert "Artifact SHA-256" in checklist
    assert "Emacs" in checklist
    assert "[ ] internal linkを選択できる" in checklist
    assert "[ ] gaiji・rare characterを識別できる" in checklist


def test_reference_report_rejects_symlink_output(tmp_path: Path) -> None:
    database = _make_reference_database(tmp_path)
    output = tmp_path / "reports"
    output.mkdir()
    target = tmp_path / "outside.json"
    target.write_text("unchanged", encoding="utf-8")
    (output / "reference-report.json").symlink_to(target)

    with pytest.raises(ReferenceReportError, match="symlink"):
        write_reference_report(database, output)

    assert target.read_text(encoding="utf-8") == "unchanged"
