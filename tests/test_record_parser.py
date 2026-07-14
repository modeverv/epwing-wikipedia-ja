from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from wikiepwing.ingest.record_parser import RecordParseError, parse_record

NORMAL_PATH = Path("tests/fixtures/enterprise/normal_articles.ndjson")
EDGE_CASE_PATH = Path("tests/fixtures/enterprise/edge_case_articles.ndjson")
EDGE_CASE_INDEX_PATH = Path("tests/fixtures/enterprise/edge_case_index.json")


def _lines(path: Path) -> list[bytes]:
    return [
        line.encode("utf-8")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _edge_index() -> dict[str, list[int]]:
    return json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))["scenarios"]


def test_parses_all_ten_normal_articles() -> None:
    lines = _lines(NORMAL_PATH)
    assert len(lines) == 10

    articles = [parse_record(line, source_sequence=i) for i, line in enumerate(lines)]

    assert [article.title for article in articles] == [
        "Emacs",
        "Linux",
        "Free Software Foundation",
        "GNU Project",
        "Text editor",
        "Operating system",
        "Unix",
        "Vi (text editor)",
        "Richard Stallman",
        "Free software",
    ]
    for article, line in zip(articles, lines, strict=True):
        assert article.namespace_id == 0
        assert article.html is not None
        assert article.wikitext is not None
        assert len(article.licenses) == 1
        assert article.licenses[0].identifier == "CC-BY-SA-4.0"
        assert article.source_hash == hashlib.sha256(line).hexdigest()


def test_normal_article_optional_fields_are_populated_when_present() -> None:
    lines = _lines(NORMAL_PATH)
    linux = parse_record(lines[1], source_sequence=1)
    stallman = parse_record(lines[8], source_sequence=8)

    assert linux.main_image is not None
    assert linux.main_image.content_url == "https://commons.wikimedia.org/wiki/File:Tux.png"
    assert stallman.redirects == ("RMS",)
    assert stallman.categories == ("Category:Richard Stallman",)
    assert stallman.templates == ("Template:Infobox person",)


def test_html_missing_wikitext_present_scenario() -> None:
    lines = _lines(EDGE_CASE_PATH)
    (index,) = _edge_index()["html_missing_wikitext_present"]

    article = parse_record(lines[index], source_sequence=index)

    assert article.html is None
    assert article.wikitext is not None


def test_same_page_id_different_revision_scenario() -> None:
    lines = _lines(EDGE_CASE_PATH)
    first_index, second_index = _edge_index()["same_page_id_different_revision"]

    first = parse_record(lines[first_index], source_sequence=first_index)
    second = parse_record(lines[second_index], source_sequence=second_index)

    assert first.page_id == second.page_id
    assert first.revision_id != second.revision_id
    assert first.source_hash != second.source_hash


def test_same_revision_duplicate_hash_scenario() -> None:
    lines = _lines(EDGE_CASE_PATH)
    first_index, second_index = _edge_index()["same_revision_duplicate_hash"]

    first = parse_record(lines[first_index], source_sequence=first_index)
    second = parse_record(lines[second_index], source_sequence=second_index)

    assert first.page_id == second.page_id
    assert first.revision_id == second.revision_id
    assert first.source_hash == second.source_hash


def test_same_revision_different_hash_scenario() -> None:
    lines = _lines(EDGE_CASE_PATH)
    first_index, second_index = _edge_index()["same_revision_different_hash"]

    first = parse_record(lines[first_index], source_sequence=first_index)
    second = parse_record(lines[second_index], source_sequence=second_index)

    assert first.page_id == second.page_id
    assert first.revision_id == second.revision_id
    assert first.source_hash != second.source_hash


def test_title_too_long_scenario_still_parses() -> None:
    lines = _lines(EDGE_CASE_PATH)
    (index,) = _edge_index()["title_too_long"]

    article = parse_record(lines[index], source_sequence=index)

    assert len(article.title.encode("utf-8")) > 1024


def test_invalid_url_scenario_still_parses() -> None:
    lines = _lines(EDGE_CASE_PATH)
    (index,) = _edge_index()["invalid_url"]

    article = parse_record(lines[index], source_sequence=index)

    assert article.url == "not-a-valid-url"


def test_empty_license_scenario() -> None:
    lines = _lines(EDGE_CASE_PATH)
    (index,) = _edge_index()["empty_license"]

    article = parse_record(lines[index], source_sequence=index)

    assert article.licenses == ()


def test_large_article_scenario_still_parses() -> None:
    lines = _lines(EDGE_CASE_PATH)
    (index,) = _edge_index()["large_article"]

    article = parse_record(lines[index], source_sequence=index)

    assert article.html is not None
    assert len(article.html.encode("utf-8")) > 2048


def test_missing_identifier_is_rejected() -> None:
    record = {
        "name": "x",
        "url": "https://x",
        "namespace": {"identifier": 0},
        "date_modified": "2026-01-01T00:00:00Z",
        "version": {"identifier": 1},
        "article_body": {},
    }
    line = json.dumps(record).encode()

    with pytest.raises(RecordParseError, match="identifier"):
        parse_record(line, source_sequence=0)


def test_missing_version_identifier_is_rejected() -> None:
    record = {
        "identifier": 1,
        "name": "x",
        "url": "https://x",
        "namespace": {"identifier": 0},
        "date_modified": "2026-01-01T00:00:00Z",
        "version": {},
        "article_body": {},
    }
    line = json.dumps(record).encode()

    with pytest.raises(RecordParseError, match="version.identifier"):
        parse_record(line, source_sequence=0)


def test_missing_article_body_is_rejected() -> None:
    record = {
        "identifier": 1,
        "name": "x",
        "url": "https://x",
        "namespace": {"identifier": 0},
        "date_modified": "2026-01-01T00:00:00Z",
        "version": {"identifier": 1},
    }
    line = json.dumps(record).encode()

    with pytest.raises(RecordParseError, match="article_body"):
        parse_record(line, source_sequence=0)


def test_invalid_date_modified_is_rejected() -> None:
    record = {
        "identifier": 1,
        "name": "x",
        "url": "https://x",
        "namespace": {"identifier": 0},
        "date_modified": "not-a-date",
        "version": {"identifier": 1},
        "article_body": {},
    }
    line = json.dumps(record).encode()

    with pytest.raises(RecordParseError, match="date_modified"):
        parse_record(line, source_sequence=0)


def test_malformed_json_is_rejected() -> None:
    with pytest.raises(RecordParseError, match="not valid JSON"):
        parse_record(b"not json at all", source_sequence=0)


def test_non_object_json_is_rejected() -> None:
    with pytest.raises(RecordParseError, match="JSON object"):
        parse_record(b"[1, 2, 3]", source_sequence=0)


def test_redirects_entry_missing_name_is_rejected() -> None:
    record = {
        "identifier": 1,
        "name": "x",
        "url": "https://x",
        "namespace": {"identifier": 0},
        "date_modified": "2026-01-01T00:00:00Z",
        "version": {"identifier": 1},
        "article_body": {},
        "redirects": [{"url": "https://x/y"}],
    }
    line = json.dumps(record).encode()

    with pytest.raises(RecordParseError, match="redirects"):
        parse_record(line, source_sequence=0)


def test_license_missing_field_is_rejected() -> None:
    record = {
        "identifier": 1,
        "name": "x",
        "url": "https://x",
        "namespace": {"identifier": 0},
        "date_modified": "2026-01-01T00:00:00Z",
        "version": {"identifier": 1},
        "article_body": {},
        "license": [{"identifier": "CC0"}],
    }
    line = json.dumps(record).encode()

    with pytest.raises(RecordParseError, match="license"):
        parse_record(line, source_sequence=0)


def test_image_without_recognizable_url_is_ignored() -> None:
    record = {
        "identifier": 1,
        "name": "x",
        "url": "https://x",
        "namespace": {"identifier": 0},
        "date_modified": "2026-01-01T00:00:00Z",
        "version": {"identifier": 1},
        "article_body": {},
        "image": {"identifier": "File:x.png"},
    }
    line = json.dumps(record).encode()

    article = parse_record(line, source_sequence=0)

    assert article.main_image is None
