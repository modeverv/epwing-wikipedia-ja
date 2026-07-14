from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.config import load_config
from wikiepwing.ingest.record_parser import RawArticle, parse_record
from wikiepwing.ingest.validate import (
    Diagnostic,
    ValidationConfigError,
    ValidationLimits,
    validate_article,
)

DEFAULT_CONFIG = Path("config/default.toml")
NORMAL_PATH = Path("tests/fixtures/enterprise/normal_articles.ndjson")
EDGE_CASE_PATH = Path("tests/fixtures/enterprise/edge_case_articles.ndjson")
EDGE_CASE_INDEX_PATH = Path("tests/fixtures/enterprise/edge_case_index.json")

LIMITS = ValidationLimits(
    max_title_bytes=4096,
    max_url_bytes=16384,
    max_html_bytes=67108864,
    max_wikitext_bytes=67108864,
    expected_namespace_id=0,
)


def _lines(path: Path) -> list[bytes]:
    return [
        line.encode("utf-8")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _edge_index() -> dict[str, list[int]]:
    return json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))["scenarios"]


def _article(**overrides: object) -> RawArticle:
    defaults: dict[str, object] = {
        "page_id": 1,
        "revision_id": 1,
        "title": "Emacs",
        "namespace_id": 0,
        "url": "https://ja.wikipedia.org/wiki/Emacs",
        "date_modified": datetime(2026, 6, 1, tzinfo=UTC),
        "html": "<p>x</p>",
        "wikitext": "x",
        "redirects": (),
        "categories": (),
        "templates": (),
        "licenses": (),
        "main_image": None,
        "source_sequence": 0,
        "source_hash": "a" * 64,
    }
    defaults.update(overrides)
    return RawArticle(**defaults)  # type: ignore[arg-type]


def test_from_config_reads_default_toml() -> None:
    config = load_config(DEFAULT_CONFIG)

    limits = ValidationLimits.from_config(config, expected_namespace_id=0)

    assert limits.max_title_bytes == 4096
    assert limits.max_url_bytes == 16384
    assert limits.max_html_bytes == 67108864
    assert limits.max_wikitext_bytes == 67108864
    assert limits.expected_namespace_id == 0


def test_valid_article_is_accepted_with_no_diagnostics() -> None:
    result = validate_article(_article(), LIMITS)

    assert result.accepted is True
    assert result.diagnostics == ()


def test_all_ten_normal_articles_are_accepted() -> None:
    lines = _lines(NORMAL_PATH)
    articles = [parse_record(line, source_sequence=i) for i, line in enumerate(lines)]

    results = [validate_article(article, LIMITS) for article in articles]

    assert all(result.accepted for result in results)
    assert all(result.diagnostics == () for result in results)


def test_title_too_long_scenario_is_rejected() -> None:
    lines = _lines(EDGE_CASE_PATH)
    (index,) = _edge_index()["title_too_long"]
    article = parse_record(lines[index], source_sequence=index)

    result = validate_article(article, LIMITS)

    assert result.accepted is False
    assert any(d.code == "REC_TITLE_TOO_LONG" for d in result.diagnostics)


def test_invalid_url_scenario_is_rejected() -> None:
    lines = _lines(EDGE_CASE_PATH)
    (index,) = _edge_index()["invalid_url"]
    article = parse_record(lines[index], source_sequence=index)

    result = validate_article(article, LIMITS)

    assert result.accepted is False
    assert any(d.code == "REC_INVALID_URL" for d in result.diagnostics)


def test_large_article_scenario_is_rejected_when_limit_is_tight() -> None:
    lines = _lines(EDGE_CASE_PATH)
    (index,) = _edge_index()["large_article"]
    article = parse_record(lines[index], source_sequence=index)
    tight_limits = ValidationLimits(
        max_title_bytes=4096,
        max_url_bytes=16384,
        max_html_bytes=2048,
        max_wikitext_bytes=67108864,
        expected_namespace_id=0,
    )

    result = validate_article(article, tight_limits)

    assert result.accepted is False
    assert any(d.code == "REC_HTML_TOO_LARGE" for d in result.diagnostics)


def test_large_article_scenario_is_accepted_under_default_limits() -> None:
    lines = _lines(EDGE_CASE_PATH)
    (index,) = _edge_index()["large_article"]
    article = parse_record(lines[index], source_sequence=index)

    result = validate_article(article, LIMITS)

    assert result.accepted is True


def test_unexpected_namespace_is_rejected() -> None:
    article = _article(namespace_id=14)

    result = validate_article(article, LIMITS)

    assert result.accepted is False
    assert any(d.code == "REC_UNEXPECTED_NAMESPACE" for d in result.diagnostics)


def test_http_url_is_rejected() -> None:
    article = _article(url="http://ja.wikipedia.org/wiki/Emacs")

    result = validate_article(article, LIMITS)

    assert result.accepted is False
    assert any(d.code == "REC_INVALID_URL" for d in result.diagnostics)


def test_url_too_long_is_rejected() -> None:
    article = _article(url="https://ja.wikipedia.org/wiki/" + "x" * 20000)
    tight_limits = ValidationLimits(
        max_title_bytes=4096,
        max_url_bytes=100,
        max_html_bytes=67108864,
        max_wikitext_bytes=67108864,
        expected_namespace_id=0,
    )

    result = validate_article(article, tight_limits)

    assert result.accepted is False
    assert any(d.code == "REC_URL_TOO_LONG" for d in result.diagnostics)


def test_wikitext_too_large_is_rejected() -> None:
    article = _article(wikitext="x" * 100)
    tight_limits = ValidationLimits(
        max_title_bytes=4096,
        max_url_bytes=16384,
        max_html_bytes=67108864,
        max_wikitext_bytes=10,
        expected_namespace_id=0,
    )

    result = validate_article(article, tight_limits)

    assert result.accepted is False
    assert any(d.code == "REC_WIKITEXT_TOO_LARGE" for d in result.diagnostics)


def test_multiple_violations_all_reported() -> None:
    article = _article(namespace_id=14, url="not-a-valid-url")

    result = validate_article(article, LIMITS)

    codes = {d.code for d in result.diagnostics}
    assert codes == {"REC_UNEXPECTED_NAMESPACE", "REC_INVALID_URL"}


def test_diagnostic_details_include_page_id() -> None:
    article = _article(namespace_id=99)

    result = validate_article(article, LIMITS)

    assert result.diagnostics[0].details["page_id"] == article.page_id


def test_negative_limit_is_rejected() -> None:
    with pytest.raises(ValidationConfigError, match="max_title_bytes"):
        ValidationLimits(
            max_title_bytes=0,
            max_url_bytes=16384,
            max_html_bytes=67108864,
            max_wikitext_bytes=67108864,
            expected_namespace_id=0,
        )


def test_invalid_diagnostic_severity_is_rejected() -> None:
    with pytest.raises(ValidationConfigError, match="severity"):
        Diagnostic(code="X", severity="ignored", message="m", details={})
