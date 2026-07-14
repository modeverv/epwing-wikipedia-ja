from __future__ import annotations

import json
import re
from pathlib import Path

FIXTURE_PATH = Path("tests/fixtures/enterprise/hundred_articles.ndjson")
_WIKI_LINK = re.compile(r'href="/wiki/([^"]+)"')


def _load_records() -> list[dict[str, object]]:
    lines = FIXTURE_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_fixture_has_one_hundred_articles() -> None:
    records = _load_records()

    assert len(records) == 100


def test_all_identifiers_are_unique() -> None:
    records = _load_records()

    identifiers = [record["identifier"] for record in records]

    assert len(set(identifiers)) == len(identifiers)


def test_records_follow_the_normal_articles_schema() -> None:
    records = _load_records()

    required_fields = {
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
    }
    for record in records:
        assert required_fields.issubset(record.keys())
        assert record["namespace"] == {"identifier": 0}
        assert isinstance(record["article_body"]["html"], str)
        assert isinstance(record["article_body"]["wikitext"], str)


def test_some_articles_have_redirects() -> None:
    records = _load_records()

    redirect_counts = [len(record["redirects"]) for record in records]

    assert any(count == 0 for count in redirect_counts)
    assert any(count >= 1 for count in redirect_counts)
    assert all(0 <= count <= 2 for count in redirect_counts)


def test_some_articles_link_to_other_fixture_titles() -> None:
    records = _load_records()
    titles = {record["name"] for record in records}

    linked_titles: set[str] = set()
    for record in records:
        html = record["article_body"]["html"]
        for match in _WIKI_LINK.findall(html):
            linked_titles.add(match.replace("_", " "))

    assert linked_titles, "expected at least one internal link across the fixture"
    assert linked_titles.issubset(titles), "internal links must target other fixture articles"


def test_generator_script_is_deterministic(tmp_path: Path) -> None:
    import importlib.util

    generator_path = Path("tests/fixtures/enterprise/generate_hundred_articles.py")
    spec = importlib.util.spec_from_file_location("generate_hundred_articles", generator_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    first = module.generate()
    second = module.generate()

    assert first == second
