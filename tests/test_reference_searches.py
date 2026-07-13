from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from wikiepwing.reference.database import connect_reference_database
from wikiepwing.reference.searches import (
    EbSearchAdapter,
    ReferenceSearchError,
    SearchHit,
    SubbookSearch,
    run_reference_searches,
)

QUERY_SET = Path(__file__).parents[1] / "config" / "query-set.toml"
MIGRATIONS = Path(__file__).parents[1] / "migrations" / "reference"


@pytest.fixture(autouse=True)
def _restore_fixture_permissions(tmp_path: Path) -> None:
    yield
    paths = sorted(tmp_path.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    for path in paths:
        if path.is_symlink():
            continue
        path.chmod(0o755 if path.is_dir() else 0o644)
    tmp_path.chmod(0o755)


def _make_reference(tmp_path: Path) -> Path:
    root = tmp_path / "reference"
    data = root / "WIKIP" / "DATA"
    data.mkdir(parents=True)
    (root / "CATALOGS").write_bytes(b"\0" * 2048)
    (data / "HONMON.EBZ").write_bytes(b"body")
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        path.chmod(0o555 if path.is_dir() else 0o444)
    root.chmod(0o555)
    return root


def _write_adapter(tmp_path: Path, body: str) -> Path:
    adapter = tmp_path / "adapter"
    adapter.write_text(f"#!/bin/sh\nset -eu\n{body}\n", encoding="utf-8")
    adapter.chmod(0o755)
    return adapter


def test_eb_search_adapter_parses_bounded_machine_output(tmp_path: Path) -> None:
    title = "日本語ウィキペディア".encode("euc_jp").hex()
    heading = "Emacs".encode("euc_jp").hex()
    executable = _write_adapter(
        tmp_path,
        f"""printf 'WIKIEPWING_EB_SEARCH\\t1\\tJISX0208\\n'
printf 'S\\t0\\twikip\\t{title}\\t1\\t0\\n'
printf 'R\\t0\\t1\\t{heading}\\t10\\t20\\t30\\t40\\n'""",
    )
    root = tmp_path / "book"
    root.mkdir()
    adapter = EbSearchAdapter(executable, timeout_seconds=2)

    result = adapter.search(root.resolve(), "word", "Emacs", 100)

    assert result == (
        SubbookSearch(
            subbook_code=0,
            directory="wikip",
            title="日本語ウィキペディア",
            returned_count=1,
            truncated=False,
            hits=(SearchHit(1, "Emacs", 10, 20, 30, 40),),
        ),
    )


@pytest.mark.parametrize(
    ("body", "kwargs", "message"),
    [
        ("sleep 2", {"timeout_seconds": 0.01}, "timed out"),
        ("echo failure >&2; exit 7", {}, "exit code 7"),
        ("printf '0123456789'", {"max_output_bytes": 5}, "output limit"),
    ],
)
def test_eb_search_adapter_reports_process_failures(
    tmp_path: Path, body: str, kwargs: dict[str, float | int], message: str
) -> None:
    executable = _write_adapter(tmp_path, body)
    root = tmp_path / "book"
    root.mkdir()
    adapter = EbSearchAdapter(executable, **kwargs)

    with pytest.raises(ReferenceSearchError, match=message):
        adapter.search(root.resolve(), "word", "Emacs", 100)


class _FixtureSearchAdapter:
    def __init__(self, *, mismatch: bool = False) -> None:
        self.mismatch = mismatch

    def search(
        self, root: Path, mode: str, query: str, max_results: int
    ) -> tuple[SubbookSearch, ...]:
        del root, max_results
        should_hit = query != "存在しない語"
        if self.mismatch and query == "Emacs" and mode == "word":
            should_hit = False
        hits = (SearchHit(1, query, 10, 20, 30, 40),) if should_hit else ()
        return (
            SubbookSearch(
                subbook_code=0,
                directory="wikip",
                title="日本語ウィキペディア",
                returned_count=len(hits),
                truncated=self.mismatch and query == "Linux" and mode == "endword",
                hits=hits,
            ),
        )


def _database_rows(database: Path) -> dict[str, list[tuple[object, ...]]]:
    queries = {
        "reference_books": (
            "book_id, source_fingerprint, catalog_path, catalog_size_bytes, "
            "inventory_sha256, identifier"
        ),
        "reference_subbooks": "subbook_id, book_id, code, title, directory",
        "reference_queries": (
            "query_id, query_key, query_text, search_mode, ordinal, expected_presence"
        ),
        "reference_query_results": (
            "query_result_id, query_id, subbook_id, rank, heading, entry_locator"
        ),
        "reference_diagnostics": (
            "diagnostic_id, book_id, subbook_id, severity, code, message, details_json"
        ),
    }
    rows: dict[str, list[tuple[object, ...]]] = {}
    with connect_reference_database(database) as connection:
        for table, columns in queries.items():
            result = connection.execute(
                f"SELECT {columns} FROM {table} ORDER BY 1"  # noqa: S608 - fixed test identifiers
            ).fetchall()
            rows[table] = [tuple(row) for row in result]
    return rows


def test_reference_searches_persist_all_fixed_queries_deterministically(
    tmp_path: Path,
) -> None:
    root = _make_reference(tmp_path)
    database = tmp_path / "reference.sqlite3"
    adapter = _FixtureSearchAdapter()

    run_reference_searches(root, QUERY_SET, database, adapter, MIGRATIONS)
    first = _database_rows(database)
    run_reference_searches(root, QUERY_SET, database, adapter, MIGRATIONS)

    assert _database_rows(database) == first
    assert len(first["reference_books"]) == 1
    assert first["reference_subbooks"] == [(1, 1, "WIKIP", "日本語ウィキペディア", "wikip")]
    assert len(first["reference_queries"]) == 18
    assert len(first["reference_query_results"]) == 16
    assert first["reference_diagnostics"] == []
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_reference_schema_preserves_duplicate_locators_at_distinct_ranks(
    tmp_path: Path,
) -> None:
    root = _make_reference(tmp_path)
    database = tmp_path / "reference.sqlite3"

    class DuplicateLocatorAdapter(_FixtureSearchAdapter):
        def search(
            self, root: Path, mode: str, query: str, max_results: int
        ) -> tuple[SubbookSearch, ...]:
            del root, mode, max_results
            hits = (
                SearchHit(1, query, 10, 20, 30, 40),
                SearchHit(2, f"{query} alias", 11, 20, 30, 40),
            )
            return (SubbookSearch(0, "wikip", "日本語ウィキペディア", 2, False, hits),)

    run_reference_searches(root, QUERY_SET, database, DuplicateLocatorAdapter(), MIGRATIONS)

    with connect_reference_database(database) as connection:
        rows = connection.execute(
            """
            SELECT rank, entry_locator
            FROM reference_query_results
            WHERE query_id = 1
            ORDER BY rank
            """
        ).fetchall()
    assert [tuple(row) for row in rows] == [(1, "30:40"), (2, "30:40")]


def test_reference_searches_persist_expectation_and_truncation_diagnostics(
    tmp_path: Path,
) -> None:
    root = _make_reference(tmp_path)
    database = tmp_path / "reference.sqlite3"

    run_reference_searches(
        root, QUERY_SET, database, _FixtureSearchAdapter(mismatch=True), MIGRATIONS
    )

    rows = _database_rows(database)
    assert [row[4] for row in rows["reference_diagnostics"]] == [
        "REF_QUERY_EXPECTATION_MISMATCH",
        "REF_QUERY_RESULTS_TRUNCATED",
    ]
