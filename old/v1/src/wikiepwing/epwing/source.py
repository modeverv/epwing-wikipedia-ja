"""Deterministic adapter input for the isolated FreePWING toolchain."""

from __future__ import annotations

from wikiepwing.model.article import Article
from wikiepwing.render.text import render_article


def freepwing_records(articles: tuple[Article, ...]) -> str:
    """Serialize title/body records in stable order for the FreePWING adapter only."""
    records: list[str] = []
    for article in sorted(articles, key=lambda item: item.title):
        body = render_article(article).replace("\r\n", "\n").replace("\r", "\n")
        records.append(f"{article.title}\t{body.replace(chr(10), '\\n')}")
        for alias in sorted(article.aliases):
            records.append(f"{alias}\t{body.replace(chr(10), '\\n')}")
    return "\n".join(records) + "\n"
