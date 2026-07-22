from __future__ import annotations

from pathlib import Path

import pytest

from wikiepwing.reference.queries import QuerySetError, load_query_set

QUERY_SET = Path(__file__).parents[1] / "config" / "query-set.toml"
JAPAN_QUERY_SET = Path(__file__).parents[1] / "config" / "japan-query-set.toml"


def test_fixed_query_set_matches_phase_two_contract() -> None:
    query_set = load_query_set(QUERY_SET)

    assert query_set.schema_version == 1
    assert query_set.identifier == "boookends-2023-baseline-v1"
    assert query_set.search_modes == ("word", "endword")
    assert query_set.max_results_per_query == 100
    assert [query.text for query in query_set.queries] == [
        "Emacs",
        "Linux",
        "日本",
        "東京都",
        "源氏物語",
        "微分積分学",
        "量子力学",
        "第二次世界大戦",
        "存在しない語",
    ]
    assert [query.ordinal for query in query_set.queries] == list(range(9))
    assert [query.expected_presence for query in query_set.queries] == [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
    ]
    assert len(query_set.sha256) == 64
    assert query_set.source_path == QUERY_SET.resolve()


def test_japan_candidate_query_set_covers_lookup_search_contract() -> None:
    query_set = load_query_set(JAPAN_QUERY_SET)

    assert query_set.identifier == "boookends-japan-candidates-v1"
    assert query_set.search_modes == ("exact", "word", "keyword")
    assert [query.text for query in query_set.queries] == [
        "日本",
        "にほん",
        "にっぽん",
        "Japan",
    ]
    assert all(query.expected_presence for query in query_set.queries)


@pytest.mark.parametrize(
    ("document", "message"),
    [
        (
            """schema_version = 1
identifier = "set"
search_modes = ["word"]
max_results_per_query = 10
unknown = true
[[queries]]
key = "one"
text = "one"
expected_presence = true
""",
            "unknown key",
        ),
        (
            """schema_version = 1
identifier = "set"
search_modes = ["word", "word"]
max_results_per_query = 10
[[queries]]
key = "one"
text = "one"
expected_presence = true
""",
            "search_modes must be unique",
        ),
        (
            """schema_version = 1
identifier = "set"
search_modes = ["word"]
max_results_per_query = 10
[[queries]]
key = "same"
text = "one"
expected_presence = true
[[queries]]
key = "same"
text = "two"
expected_presence = true
""",
            "duplicate query key",
        ),
        (
            """schema_version = 1
identifier = "set"
search_modes = ["word"]
max_results_per_query = 10
[[queries]]
key = "one"
text = "bad\\nquery"
expected_presence = true
""",
            "control character",
        ),
        (
            """schema_version = 1
identifier = "set"
search_modes = ["word"]
max_results_per_query = 10
[[queries]]
key = "one"
text = "one"
expected_presence = 1
""",
            "expected_presence must be a boolean",
        ),
    ],
)
def test_invalid_query_documents_are_rejected(tmp_path: Path, document: str, message: str) -> None:
    path = tmp_path / "queries.toml"
    path.write_text(document, encoding="utf-8")

    with pytest.raises(QuerySetError, match=message):
        load_query_set(path)


def test_query_set_rejects_symlink_and_size_limit(tmp_path: Path) -> None:
    target = tmp_path / "queries.toml"
    target.write_text("schema_version = 1\n", encoding="utf-8")
    link = tmp_path / "link.toml"
    link.symlink_to(target)

    with pytest.raises(QuerySetError, match="must not be a symlink"):
        load_query_set(link)
    with pytest.raises(QuerySetError, match="size limit"):
        load_query_set(target, max_bytes=5)


def test_query_set_rejects_overlong_utf8_query(tmp_path: Path) -> None:
    path = tmp_path / "queries.toml"
    path.write_text(
        """schema_version = 1
identifier = "set"
search_modes = ["word"]
max_results_per_query = 10
[[queries]]
key = "long"
text = "あああ"
expected_presence = true
""",
        encoding="utf-8",
    )

    with pytest.raises(QuerySetError, match="UTF-8 byte limit"):
        load_query_set(path, max_query_bytes=8)
