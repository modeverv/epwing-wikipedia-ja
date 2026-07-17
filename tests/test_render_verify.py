from __future__ import annotations

import json
from pathlib import Path

import pytest

from wikiepwing.pipeline.progress import PhaseProgress
from wikiepwing.render.verify import EntriesVerificationError, verify_entries_jsonl


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )


def test_verify_entries_jsonl_accepts_valid_entries(tmp_path: Path) -> None:
    path = tmp_path / "entries.jsonl"
    _write_jsonl(
        path,
        [
            {
                "tag": "p1",
                "title": "Emacs",
                "aliases": ["GNU Emacs"],
                "body": "x",
                "targets": ["p2"],
            },
            {"tag": "p2", "title": "Linux", "aliases": [], "body": "y", "targets": []},
        ],
    )

    result = verify_entries_jsonl(path)

    assert result.ok is True
    assert result.entry_count == 2
    assert result.issues == ()


def test_verify_entries_jsonl_tolerates_unicode_line_separators_in_body(tmp_path: Path) -> None:
    # U+2029 PARAGRAPH SEPARATOR is a valid, unescaped character inside a JSON
    # string and real Wikipedia article bodies contain it; str.splitlines()
    # (unlike JSONL's actual "\n"-only record separator) treats it as a line
    # break and previously shredded this single record into invalid fragments.
    path = tmp_path / "entries.jsonl"
    _write_jsonl(
        path,
        [
            {
                "tag": "p1",
                "title": "X",
                "aliases": [],
                "body": "before after",
                "targets": [],
            }
        ],
    )

    result = verify_entries_jsonl(path)

    assert result.ok is True
    assert result.entry_count == 1


def test_verify_entries_jsonl_detects_empty_tag(tmp_path: Path) -> None:
    path = tmp_path / "entries.jsonl"
    _write_jsonl(path, [{"tag": "", "title": "X", "aliases": [], "body": "", "targets": []}])

    result = verify_entries_jsonl(path)

    assert result.ok is False
    assert any(issue.code == "EMPTY_TAG" for issue in result.issues)


def test_verify_entries_jsonl_detects_empty_title(tmp_path: Path) -> None:
    path = tmp_path / "entries.jsonl"
    _write_jsonl(path, [{"tag": "p1", "title": "", "aliases": [], "body": "", "targets": []}])

    result = verify_entries_jsonl(path)

    assert result.ok is False
    assert any(issue.code == "EMPTY_TITLE" for issue in result.issues)


def test_verify_entries_jsonl_detects_duplicate_tag(tmp_path: Path) -> None:
    path = tmp_path / "entries.jsonl"
    _write_jsonl(
        path,
        [
            {"tag": "p1", "title": "A", "aliases": [], "body": "", "targets": []},
            {"tag": "p1", "title": "B", "aliases": [], "body": "", "targets": []},
        ],
    )

    result = verify_entries_jsonl(path)

    assert result.ok is False
    assert any(issue.code == "DUPLICATE_TAG" for issue in result.issues)


def test_verify_entries_jsonl_detects_duplicate_headword_across_entries(tmp_path: Path) -> None:
    path = tmp_path / "entries.jsonl"
    _write_jsonl(
        path,
        [
            {"tag": "p1", "title": "Shared", "aliases": [], "body": "", "targets": []},
            {"tag": "p2", "title": "Other", "aliases": ["Shared"], "body": "", "targets": []},
        ],
    )

    result = verify_entries_jsonl(path)

    assert result.ok is False
    assert any(issue.code == "DUPLICATE_HEADWORD" for issue in result.issues)


def test_verify_entries_jsonl_allows_same_headword_within_one_entry(tmp_path: Path) -> None:
    path = tmp_path / "entries.jsonl"
    _write_jsonl(
        path,
        [{"tag": "p1", "title": "Same", "aliases": ["Same"], "body": "", "targets": []}],
    )

    result = verify_entries_jsonl(path)

    assert result.ok is True


def test_verify_entries_jsonl_detects_unknown_target(tmp_path: Path) -> None:
    path = tmp_path / "entries.jsonl"
    _write_jsonl(
        path,
        [{"tag": "p1", "title": "A", "aliases": [], "body": "", "targets": ["pmissing"]}],
    )

    result = verify_entries_jsonl(path)

    assert result.ok is False
    assert any(issue.code == "UNKNOWN_TARGET" for issue in result.issues)


def test_verify_entries_jsonl_handles_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "entries.jsonl"
    path.write_text("", encoding="utf-8")

    result = verify_entries_jsonl(path)

    assert result.ok is True
    assert result.entry_count == 0


def test_verify_entries_jsonl_completes_all_progress_phases_for_invalid_records(
    tmp_path: Path,
) -> None:
    path = tmp_path / "entries.jsonl"
    _write_jsonl(
        path,
        [
            {"tag": "", "title": "X", "aliases": [], "body": "", "targets": []},
            {"tag": "p2", "title": "Y", "aliases": [], "body": "", "targets": "bad"},
        ],
    )
    progress: list[PhaseProgress] = []

    verify_entries_jsonl(path, on_progress=progress.append)

    completed_phases = {item.phase for item in progress if item.complete}
    assert completed_phases == {
        "verify-entries-read",
        "verify-entries-tags",
        "verify-entries-headwords",
        "verify-entries-targets",
    }


def test_verify_entries_jsonl_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "entries.jsonl"
    path.write_text("{not json}\n", encoding="utf-8")

    with pytest.raises(EntriesVerificationError, match="invalid JSON"):
        verify_entries_jsonl(path)


def test_verify_entries_jsonl_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(EntriesVerificationError, match="cannot read"):
        verify_entries_jsonl(tmp_path / "missing.jsonl")
