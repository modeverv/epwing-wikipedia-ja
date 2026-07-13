"""Export raw stored pages through parsing and rendering adapter boundaries."""

from __future__ import annotations

from pathlib import Path

from wikiepwing.mediawiki.parser import parse_article
from wikiepwing.render.text import render_article
from wikiepwing.storage.database import RawPageStore


def export_records(database_path: Path, destination: Path) -> int:
    """Write deterministic backend records from raw SQLite pages."""
    store = RawPageStore(database_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    count = 0
    try:
        with temporary.open("w", encoding="utf-8") as target:
            for page in store.pages():
                article = parse_article(page.page_id, page.title, page.text)
                body = render_article(article).replace("\r\n", "\n").replace("\r", "\n")
                rendered = body.replace("\n", "\\n")
                target.write(f"{article.title}\t{rendered}\n")
                for alias in sorted(article.aliases):
                    target.write(f"{alias}\t{rendered}\n")
                count += 1
    finally:
        store.close()
    temporary.replace(destination)
    return count
