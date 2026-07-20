"""Readable constrained-viewer layout for semantic articles."""

from __future__ import annotations

import base64

from wikiepwing.model.article import Article, Block


def _image_token(file_name: str, caption: str) -> str:
    encoded_name = base64.urlsafe_b64encode(file_name.encode()).decode().rstrip("=")
    encoded_caption = base64.urlsafe_b64encode(caption.encode()).decode().rstrip("=")
    return f"@@IMAGE:{encoded_name}:{encoded_caption}@@"


def _block_text(block: Block) -> str:
    return "".join(inline.text for inline in block.inlines).strip()


def render_article(article: Article) -> str:
    """Render source-order blocks without exposing parser or backend internals."""
    lines = [article.title]
    if article.aliases:
        lines.extend(("Aliases: " + ", ".join(article.aliases), ""))
    if article.media:
        lines.extend(
            (
                "Images:",
                *(
                    f"- {_image_token(item.file_name, item.caption)} {item.file_name}"
                    + (f" - {item.caption}" if item.caption else "")
                    for item in article.media
                ),
                "",
            )
        )
    for block in article.blocks:
        text = _block_text(block)
        if block.kind == "heading":
            lines.extend((f"{'#' * (block.level or 1)} {text}", ""))
        elif block.kind == "rule":
            lines.extend(("-" * 20, ""))
        elif text:
            lines.extend((text, ""))
    return "\n".join(lines).rstrip() + "\n"
