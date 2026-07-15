#!/usr/bin/env python3
"""Deterministically generate ten_thousand_articles.ndjson (TASK-P006).

Synthetic data following the same Wikimedia Enterprise NDJSON schema as
tests/fixtures/enterprise/normal_articles.ndjson (TASK-D010), scaled to
10,000 articles for end-to-end testing (TASK-P007). Re-running this
script produces byte-identical output.
"""

from __future__ import annotations

import json
from pathlib import Path

FIRST_PAGE_ID = 930001
ARTICLE_COUNT = 10000

_TOPICS = [
    "Emacs",
    "Vim",
    "Linux",
    "Unix",
    "GNU Project",
    "Free Software Foundation",
    "Richard Stallman",
    "Text editor",
    "Operating system",
    "Free software",
    "Open source",
    "Kernel",
    "Compiler",
    "Interpreter",
    "Debugger",
    "Version control",
    "Git",
    "Software license",
    "Copyleft",
    "Programming language",
]
_CATEGORIES = [
    "Free software",
    "Software",
    "Computing",
    "Operating systems",
    "Programming",
]
_LICENSE = {
    "identifier": "CC-BY-SA-4.0",
    "name": "Creative Commons Attribution-ShareAlike License 4.0",
    "url": "https://creativecommons.org/licenses/by-sa/4.0/",
}


def _title_for(index: int) -> str:
    topic = _TOPICS[index % len(_TOPICS)]
    generation = index // len(_TOPICS)
    return topic if generation == 0 else f"{topic} ({generation + 1})"


def _url_for(title: str) -> str:
    return "https://ja.wikipedia.org/wiki/" + title.replace(" ", "_")


def _build_article(index: int) -> dict[str, object]:
    page_id = FIRST_PAGE_ID + index
    title = _title_for(index)
    url = _url_for(title)

    link_targets = [
        _title_for((index + offset) % ARTICLE_COUNT)
        for offset in (1, 7, 13)
        if (index + offset) % ARTICLE_COUNT != index
    ]
    link_targets = list(dict.fromkeys(link_targets))[: 1 + (index % 3)]
    links_html = "".join(
        f' <a href="/wiki/{target.replace(" ", "_")}">{target}</a>' for target in link_targets
    )
    html = (
        f"<!DOCTYPE html><html><body><p>{title}についての説明です。{links_html}</p></body></html>"
    )
    wikitext = f"'''{title}'''\n\n{title}についての説明です。"

    redirects = []
    if index % 3 != 0:
        redirects.append({"name": f"{title} alias", "url": url + "_alias"})
    if index % 7 == 0:
        redirects.append({"name": f"{title} redirect2", "url": url + "_redirect2"})

    categories = [
        {
            "name": f"Category:{_CATEGORIES[(index + offset) % len(_CATEGORIES)]}",
            "url": "https://ja.wikipedia.org/wiki/Category:"
            + _CATEGORIES[(index + offset) % len(_CATEGORIES)].replace(" ", "_"),
        }
        for offset in range(1 + (index % 2))
    ]

    record: dict[str, object] = {
        "identifier": page_id,
        "name": title,
        "url": url,
        "namespace": {"identifier": 0},
        "in_language": {
            "identifier": "ja",
            "name": "Japanese",
            "alternate_name": "日本語",
            "direction": "ltr",
        },
        "is_part_of": {
            "identifier": "jawiki",
            "code": "wiki",
            "name": "Wikipedia",
            "url": "https://ja.wikipedia.org",
            "in_language": {"identifier": "ja"},
        },
        "date_modified": "2026-06-01T00:00:00Z",
        "version": {
            "identifier": 1900000 + index,
            "editor": {"identifier": 1, "name": "TestEditor"},
            "comment": "fixture revision",
            "scores": {},
            "size": {"unit_text": "B", "value": 512},
        },
        "article_body": {"html": html, "wikitext": wikitext},
        "license": [_LICENSE],
        "redirects": redirects,
        "categories": categories,
        "templates": [
            {"name": "Template:Infobox", "url": "https://ja.wikipedia.org/wiki/Template:Infobox"}
        ],
    }
    if index % 11 == 0:
        record["image"] = {
            "identifier": f"File:{title.replace(' ', '_')}.png",
            "url": f"https://commons.wikimedia.org/wiki/File:{title.replace(' ', '_')}.png",
        }
    return record


def generate() -> list[dict[str, object]]:
    """Return the 10,000 deterministic article records."""
    return [_build_article(index) for index in range(ARTICLE_COUNT)]


def main() -> None:
    """Write ten_thousand_articles.ndjson next to this script."""
    destination = Path(__file__).parent / "ten_thousand_articles.ndjson"
    with destination.open("w", encoding="utf-8") as handle:
        for record in generate():
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


if __name__ == "__main__":
    main()
