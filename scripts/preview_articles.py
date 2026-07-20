#!/usr/bin/env python3
"""Generate HTML preview of rendered EPWING articles (TASK-T039)."""

import html
import sqlite3
import sys
from pathlib import Path

import zstandard

from wikiepwing.model.canonical import decode_article
from wikiepwing.render.mini_layout import render_article_to_entry
from wikiepwing.render.render_node import (
    GraphicRenderNode,
    LineBreakRenderNode,
    LinkRenderNode,
    TextRenderNode,
)


def generate_preview(
    database_path: Path,
    output_path: Path,
    target_titles: tuple[str, ...] = ("日本", "Emacs", "チューリップ", "JavaScript"),
) -> None:
    if not database_path.is_file():
        print(f"Error: model database non-existent: {database_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(database_path)
    dctx = zstandard.ZstdDecompressor()
    cursor = conn.cursor()

    articles = []
    seen_ids = set()

    for title in target_titles:
        query = (
            "SELECT page_id, article_json_zstd FROM articles "
            "WHERE title = ? OR title LIKE ? LIMIT 1"
        )
        cursor.execute(query, (title, f"%{title}%"))
        row = cursor.fetchone()
        if row and row[0] not in seen_ids:
            seen_ids.add(row[0])
            raw_json = dctx.decompress(row[1])
            articles.append(decode_article(raw_json))

    if len(articles) < 3:
        cursor.execute("SELECT page_id, article_json_zstd FROM articles LIMIT 5")
        for row in cursor.fetchall():
            if row[0] not in seen_ids:
                seen_ids.add(row[0])
                raw_json = dctx.decompress(row[1])
                articles.append(decode_article(raw_json))

    conn.close()

    css_style = (
        "body { font-family: sans-serif; background: #1e1e1e; color: #d4d4d4; padding: 20px; }\n"
        ".article { background: #252526; border: 1px solid #454545; "
        "padding: 20px; margin-bottom: 30px; border-radius: 8px; }\n"
        "h1 { color: #569cd6; border-bottom: 1px solid #454545; padding-bottom: 10px; }\n"
        "h2 { color: #4ec9b0; margin-top: 0; }\n"
        "pre { white-space: pre-wrap; word-wrap: break-word; font-family: monospace; "
        "font-size: 13px; line-height: 1.6; background: #181818; padding: 15px; "
        "border-radius: 6px; border: 1px solid #333; color: #ce9178; }\n"
    )

    html_out = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'><title>EPWING Article Preview</title>",
        f"<style>{css_style}</style></head><body>",
        f"<h1>EPWING 本文レンダリング プレビュー ({len(articles)} 記事)</h1>",
    ]

    for article in articles:
        entry = render_article_to_entry(article)
        rendered_text_parts = []
        for node in entry.body:
            if isinstance(node, TextRenderNode):
                rendered_text_parts.append(node.text)
            elif isinstance(node, LinkRenderNode):
                rendered_text_parts.append(f"[{node.label}]")
            elif isinstance(node, GraphicRenderNode):
                rendered_text_parts.append(f"【画像: {node.name}】")
            elif isinstance(node, LineBreakRenderNode):
                rendered_text_parts.append("\n")

        full_text = "".join(rendered_text_parts)
        escaped_text = html.escape(full_text)

        html_out.append("<div class='article'>")
        html_out.append(
            f"<h2>記事タイトル: {html.escape(article.title)} (Page ID: {article.page_id})</h2>"
        )
        html_out.append(f"<pre>{escaped_text}</pre>")
        html_out.append("</div>")

    html_out.append("</body></html>")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(html_out), encoding="utf-8")
    print(f"Wrote preview for {len(articles)} articles to {output_path}")


if __name__ == "__main__":
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/work/model-diff-ram8.sqlite3")
    if not db_path.exists():
        db_path = Path("data/work/model.sqlite3")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("preview_articles.html")
    generate_preview(db_path, out_path)
