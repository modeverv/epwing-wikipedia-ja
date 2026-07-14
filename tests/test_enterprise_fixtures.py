from __future__ import annotations

import json
from pathlib import Path

FIXTURES_DIR = Path("tests/fixtures/enterprise")
NORMAL_PATH = FIXTURES_DIR / "normal_articles.ndjson"
EDGE_CASE_PATH = FIXTURES_DIR / "edge_case_articles.ndjson"
EDGE_CASE_INDEX_PATH = FIXTURES_DIR / "edge_case_index.json"

REQUIRED_FIELDS = (
    "identifier",
    "name",
    "url",
    "namespace",
    "in_language",
    "is_part_of",
    "date_modified",
    "version",
    "article_body",
    "license",
    "redirects",
    "categories",
    "templates",
)

_SECRET_MARKERS = (
    "WME_USERNAME",
    "WME_PASSWORD",
    "WME_ACCESS_TOKEN",
    "WME_REFRESH_TOKEN",
    "Bearer ",
)


def _load_ndjson(path: Path) -> list[dict[str, object]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        assert isinstance(record, dict)
        records.append(record)
    return records


def _assert_no_secrets(raw_text: str) -> None:
    for marker in _SECRET_MARKERS:
        assert marker not in raw_text, f"fixture must not contain {marker!r}"


def test_normal_fixture_has_ten_valid_articles() -> None:
    raw_text = NORMAL_PATH.read_text(encoding="utf-8")
    _assert_no_secrets(raw_text)
    records = _load_ndjson(NORMAL_PATH)

    assert len(records) == 10
    identifiers = [record["identifier"] for record in records]
    assert len(identifiers) == len(set(identifiers)), "normal fixture must not duplicate page IDs"
    for record in records:
        for field in REQUIRED_FIELDS:
            assert field in record, f"missing field {field!r} in {record.get('name')!r}"
        assert isinstance(record["namespace"], dict) and "identifier" in record["namespace"]
        assert isinstance(record["version"], dict) and "identifier" in record["version"]
        assert (
            isinstance(record["is_part_of"], dict)
            and record["is_part_of"]["identifier"] == "jawiki"
        )
        assert record["article_body"].get("html") or record["article_body"].get("wikitext")


def test_normal_fixture_titles_are_unique() -> None:
    records = _load_ndjson(NORMAL_PATH)
    titles = [record["name"] for record in records]
    assert len(titles) == len(set(titles))


def test_edge_case_fixture_has_no_secrets() -> None:
    _assert_no_secrets(EDGE_CASE_PATH.read_text(encoding="utf-8"))


def test_edge_case_index_matches_fixture_content() -> None:
    records = _load_ndjson(EDGE_CASE_PATH)
    index = json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))
    scenarios = index["scenarios"]

    expected_scenarios = {
        "html_missing_wikitext_present",
        "same_page_id_different_revision",
        "same_revision_duplicate_hash",
        "same_revision_different_hash",
        "title_too_long",
        "invalid_url",
        "empty_license",
        "large_article",
    }
    assert set(scenarios.keys()) == expected_scenarios

    all_referenced_indexes = [index for indexes in scenarios.values() for index in indexes]
    assert min(all_referenced_indexes) >= 0
    assert max(all_referenced_indexes) < len(records)


def test_html_missing_wikitext_present_scenario() -> None:
    records = _load_ndjson(EDGE_CASE_PATH)
    index = json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))
    (line,) = index["scenarios"]["html_missing_wikitext_present"]
    record = records[line]

    assert "html" not in record["article_body"]
    assert record["article_body"]["wikitext"]


def test_same_page_id_different_revision_scenario() -> None:
    records = _load_ndjson(EDGE_CASE_PATH)
    index = json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))
    first_index, second_index = index["scenarios"]["same_page_id_different_revision"]
    first, second = records[first_index], records[second_index]

    assert first["identifier"] == second["identifier"]
    assert first["version"]["identifier"] != second["version"]["identifier"]
    assert first["article_body"]["html"] != second["article_body"]["html"]


def test_same_revision_duplicate_hash_scenario() -> None:
    records = _load_ndjson(EDGE_CASE_PATH)
    index = json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))
    first_index, second_index = index["scenarios"]["same_revision_duplicate_hash"]
    first, second = records[first_index], records[second_index]

    assert first["identifier"] == second["identifier"]
    assert first["version"]["identifier"] == second["version"]["identifier"]
    assert first == second, "duplicate scenario must deliver byte-identical records"


def test_same_revision_different_hash_scenario() -> None:
    records = _load_ndjson(EDGE_CASE_PATH)
    index = json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))
    first_index, second_index = index["scenarios"]["same_revision_different_hash"]
    first, second = records[first_index], records[second_index]

    assert first["identifier"] == second["identifier"]
    assert first["version"]["identifier"] == second["version"]["identifier"]
    assert first["article_body"]["html"] != second["article_body"]["html"]


def test_title_too_long_scenario() -> None:
    records = _load_ndjson(EDGE_CASE_PATH)
    index = json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))
    (line,) = index["scenarios"]["title_too_long"]
    record = records[line]

    assert len(record["name"].encode("utf-8")) > 1024


def test_invalid_url_scenario() -> None:
    records = _load_ndjson(EDGE_CASE_PATH)
    index = json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))
    (line,) = index["scenarios"]["invalid_url"]
    record = records[line]

    assert not record["url"].startswith("https://")


def test_empty_license_scenario() -> None:
    records = _load_ndjson(EDGE_CASE_PATH)
    index = json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))
    (line,) = index["scenarios"]["empty_license"]
    record = records[line]

    assert record["license"] == []


def test_large_article_scenario() -> None:
    records = _load_ndjson(EDGE_CASE_PATH)
    index = json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))
    (line,) = index["scenarios"]["large_article"]
    record = records[line]

    assert len(record["article_body"]["html"].encode("utf-8")) > 2048
