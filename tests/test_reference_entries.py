from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from wikiepwing.reference.database import (
    connect_reference_database,
    initialize_reference_database,
)
from wikiepwing.reference.entries import (
    EbEntryAdapter,
    EntrySample,
    ReferenceEntryError,
    sample_reference_entries,
)

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "reference"


def _write_adapter(tmp_path: Path, body: str) -> Path:
    adapter = tmp_path / "adapter"
    adapter.write_text(f"#!/bin/sh\nset -eu\n{body}\n", encoding="utf-8")
    adapter.chmod(0o755)
    return adapter


def test_eb_entry_adapter_parses_text_and_hook_counts(tmp_path: Path) -> None:
    text = "Emacsはテキストエディタです。".encode("euc_jp").hex()
    executable = _write_adapter(
        tmp_path,
        f"""printf 'WIKIEPWING_EB_ENTRY\\t1\\tJISX0208\\n'
printf 'E\\twikip\\t30\\t40\\t0\\t{text}\\t3\\t2\\t4\\t5\\n'""",
    )
    root = tmp_path / "book"
    root.mkdir()
    adapter = EbEntryAdapter(executable, timeout_seconds=2)

    sample = adapter.read(root.resolve(), "wikip", 30, 40, 262144)

    assert sample == EntrySample(
        text="Emacsはテキストエディタです。",
        truncated=False,
        reference_count=3,
        image_count=2,
        narrow_gaiji_count=4,
        wide_gaiji_count=5,
    )


def test_eb_entry_adapter_rejects_invalid_protocol(tmp_path: Path) -> None:
    executable = _write_adapter(
        tmp_path,
        "printf 'WIKIEPWING_EB_ENTRY\\t1\\tJISX0208\\n"
        "E\\twikip\\t30\\t40\\t2\\t00\\t0\\t0\\t0\\t0\\n'",
    )
    root = tmp_path / "book"
    root.mkdir()

    with pytest.raises(ReferenceEntryError, match="invalid adapter entry record"):
        EbEntryAdapter(executable).read(root.resolve(), "wikip", 30, 40, 262144)


def _make_search_database(tmp_path: Path) -> Path:
    database = initialize_reference_database(tmp_path / "reference.sqlite3", MIGRATIONS)
    with connect_reference_database(database) as connection:
        connection.execute(
            """
            INSERT INTO reference_books (
                source_fingerprint, catalog_path, catalog_size_bytes, inventory_sha256, identifier
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("a" * 64, "CATALOGS", 2048, "b" * 64, "fixture"),
        )
        connection.execute(
            """
            INSERT INTO reference_subbooks (book_id, code, title, directory)
            VALUES (1, 'WIKIP', '日本語ウィキペディア', 'wikip')
            """
        )
        for query_id, (key, text, mode, ordinal) in enumerate(
            (
                ("emacs:word", "Emacs", "word", 0),
                ("emacs:endword", "Emacs", "endword", 1),
                ("linux:word", "Linux", "word", 2),
            ),
            start=1,
        ):
            connection.execute(
                """
                INSERT INTO reference_queries (
                    query_id, query_key, query_text, search_mode, ordinal, expected_presence
                ) VALUES (?, ?, ?, ?, ?, 1)
                """,
                (query_id, key, text, mode, ordinal),
            )
        connection.executemany(
            """
            INSERT INTO reference_query_results (
                query_id, subbook_id, rank, heading, entry_locator
            ) VALUES (?, 1, 1, ?, ?)
            """,
            ((1, "Emacs", "30:40"), (2, "Emacs alias", "30:40"), (3, "Linux", "50:60")),
        )
    return database


class _FixtureEntryAdapter:
    def __init__(self, *, truncated: bool = False) -> None:
        self.truncated = truncated
        self.calls: list[tuple[str, int, int]] = []

    def read(
        self, root: Path, subbook_directory: str, page: int, offset: int, max_bytes: int
    ) -> EntrySample:
        del root, max_bytes
        self.calls.append((subbook_directory, page, offset))
        return EntrySample(
            text=f"sample at {page}:{offset}",
            truncated=self.truncated and page == 50,
            reference_count=page // 10,
            image_count=1,
            narrow_gaiji_count=2,
            wide_gaiji_count=3,
        )


class _FailingFixtureEntryAdapter(_FixtureEntryAdapter):
    def read(
        self, root: Path, subbook_directory: str, page: int, offset: int, max_bytes: int
    ) -> EntrySample:
        if page == 50:
            raise ReferenceEntryError("fixture entry is unreadable")
        return super().read(root, subbook_directory, page, offset, max_bytes)


def _entry_rows(database: Path) -> tuple[list[tuple[object, ...]], list[str]]:
    with connect_reference_database(database) as connection:
        entries = connection.execute(
            """
            SELECT entry_locator, title, body_excerpt, body_sha256, body_byte_count,
                   internal_link_count, image_count, gaiji_count
            FROM reference_entries
            ORDER BY entry_id
            """
        ).fetchall()
        diagnostics = connection.execute(
            """
            SELECT code FROM reference_diagnostics
            WHERE code LIKE 'REF_ENTRY_%' OR code LIKE 'REF_MANUAL_%'
            ORDER BY diagnostic_id
            """
        ).fetchall()
    return [tuple(row) for row in entries], [row[0] for row in diagnostics]


def test_entry_sampling_deduplicates_rank_one_locators_and_is_idempotent(
    tmp_path: Path,
) -> None:
    database = _make_search_database(tmp_path)
    root = tmp_path / "reference"
    root.mkdir()
    adapter = _FixtureEntryAdapter()

    sample_reference_entries(database, root.resolve(), adapter)
    first = _entry_rows(database)
    first_hash = hashlib.sha256(database.read_bytes()).hexdigest()
    sample_reference_entries(database, root.resolve(), adapter)

    assert _entry_rows(database) == first
    assert hashlib.sha256(database.read_bytes()).hexdigest() == first_hash
    assert adapter.calls == [("wikip", 30, 40), ("wikip", 50, 60)] * 2
    assert [row[0] for row in first[0]] == ["30:40", "50:60"]
    assert first[0][0][1] == "Emacs"
    assert first[0][0][3] == hashlib.sha256(b"sample at 30:40").hexdigest()
    assert first[0][0][5:] == (3, 1, 5)
    assert first[1] == ["REF_MANUAL_VIEWER_RENDER_REQUIRED"]


def test_entry_sampling_records_truncation_diagnostic(tmp_path: Path) -> None:
    database = _make_search_database(tmp_path)
    root = tmp_path / "reference"
    root.mkdir()

    sample_reference_entries(database, root.resolve(), _FixtureEntryAdapter(truncated=True))

    assert _entry_rows(database)[1] == [
        "REF_ENTRY_TEXT_TRUNCATED",
        "REF_MANUAL_VIEWER_RENDER_REQUIRED",
    ]


def test_entry_sampling_records_recoverable_read_failure(tmp_path: Path) -> None:
    database = _make_search_database(tmp_path)
    root = tmp_path / "reference"
    root.mkdir()

    sample_reference_entries(database, root.resolve(), _FailingFixtureEntryAdapter())

    entries, diagnostics = _entry_rows(database)
    assert [row[0] for row in entries] == ["30:40"]
    assert diagnostics == ["REF_ENTRY_READ_FAILED", "REF_MANUAL_VIEWER_RENDER_REQUIRED"]
