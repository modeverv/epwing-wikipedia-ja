"""Conservative Wikitext-to-model conversion with readable fallbacks."""

from __future__ import annotations

import re

from wikiepwing.mediawiki.media import extract_media_references, strip_file_links
from wikiepwing.mediawiki.tables import parse_table, render_table
from wikiepwing.mediawiki.templates import render_template
from wikiepwing.model.article import Article, Block, Inline

COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
EXTERNAL_LINK = re.compile(r"\[(?:https?|ftp)://[^\s\]]+(?:\s+([^\]]+))?\]")
HEADING = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$")
HTML_TAG = re.compile(
    r"</?(?:small|span|div|center|nowiki|includeonly|noinclude|onlyinclude)[^>]*>"
)
LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
REF = re.compile(r"<ref\b[^>]*>.*?</ref\s*>|<ref\b[^>]*/\s*>", re.DOTALL | re.IGNORECASE)
TAG_BREAK = re.compile(r"<br\s*/?>|</?(?:p|li|tr|td|th|h[1-6])[^>]*>", re.IGNORECASE)


def _split_arguments(source: str) -> list[str]:
    """Split a template body on top-level pipes only."""
    parts: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(source):
        if source[index : index + 2] == "{{":
            depth += 1
        elif source[index : index + 2] == "}}" and depth:
            depth -= 1
        elif char == "|" and depth == 0:
            parts.append(source[start:index])
            start = index + 1
    parts.append(source[start:])
    return parts


def _template_text(body: str) -> str:
    parts = _split_arguments(body)
    name = parts[0].strip()
    positional: list[str] = []
    named: list[tuple[str, str]] = []
    for part in parts[1:]:
        key, separator, value = part.partition("=")
        if separator:
            named.append((key.strip(), value.strip()))
        else:
            positional.append(part.strip())

    normalized = name.replace("_", " ").strip().casefold()
    if normalized.startswith("infobox"):
        ignored = {
            "image",
            "画像",
            "画像説明",
            "logo",
            "logo size",
            "logo caption",
            "ロゴ",
            "ロゴサイズ",
            "ロゴ説明",
            "背景色",
            "class",
            "style",
            "caption",
            "module",
            "embed",
            "channel_url",
            "channel_display_name",
            "years active",
            "genre",
            "subscribers",
            "views",
            "stats_update",
        }
        lines = [
            f"【{key}】{value}"
            for key, value in named
            if key and value and key.casefold() not in ignored
        ]
        return "\n\n".join(lines)
    if normalized in {"jpn", "flagicon", "flagiconjpn"}:
        return ""
    if normalized in {"r", "sfn", "harv", "harvnb"} or normalized.startswith(
        ("cite ", "citation", "refn", "reflist")
    ):
        return ""
    if normalized == "otheruses" and positional:
        return f"「{positional[0]}」のその他の用法については、関連項目を参照。"
    if normalized in {"生年月日と年齢", "生年月日"} and len(positional) >= 3:
        return f"{positional[0]}年{positional[1]}月{positional[2]}日"
    return render_template(name, tuple(positional), tuple(named)).text


def _replace_templates(source: str) -> str:
    """Resolve balanced templates from the inside out without executing them."""
    result = source
    while "{{" in result:
        start = result.rfind("{{")
        end = result.find("}}", start)
        if end < 0:
            return result.replace("{{", "")
        result = result[:start] + _template_text(result[start + 2 : end]) + result[end + 2 :]
    return result


def _replace_tables(source: str) -> str:
    lines = source.splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].lstrip().startswith("{|"):
            end = index + 1
            while end < len(lines) and not lines[end].lstrip().startswith("|}"):
                end += 1
            if end < len(lines):
                table = render_table(parse_table("\n".join(lines[index : end + 1])))
                if table:
                    output.extend((table, ""))
                index = end + 1
                continue
        output.append(lines[index])
        index += 1
    return "\n".join(output)


def _clean_wikitext(source: str) -> str:
    """Remove presentation syntax while preserving readable article information."""
    cleaned = COMMENT.sub("", source)
    cleaned = strip_file_links(cleaned)
    cleaned = REF.sub("", cleaned)
    cleaned = _replace_tables(cleaned)
    cleaned = _replace_templates(cleaned)
    cleaned = TAG_BREAK.sub("\n", cleaned)
    cleaned = HTML_TAG.sub("", cleaned)
    cleaned = EXTERNAL_LINK.sub(lambda match: match.group(1) or "", cleaned)
    cleaned = cleaned.replace("'''", "").replace("''", "")
    return cleaned


def _inlines(text: str) -> tuple[Inline, ...]:
    parts: list[Inline] = []
    cursor = 0
    for match in LINK.finditer(text):
        if match.start() > cursor:
            parts.append(Inline(text[cursor : match.start()]))
        target = match.group(1).strip()
        parts.append(Inline((match.group(2) or target).strip(), target))
        cursor = match.end()
    if cursor < len(text):
        parts.append(Inline(text[cursor:]))
    return tuple(
        Inline(part.text.replace("[[", "").replace("]]", ""), part.target) for part in parts
    )


def parse_article(page_id: int, title: str, wikitext: str) -> Article:
    """Parse Wikitext into readable blocks without executing source content."""
    media = extract_media_references(wikitext)
    blocks: list[Block] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            blocks.append(Block("paragraph", _inlines(" ".join(paragraph))))
            paragraph.clear()

    for raw_line in _clean_wikitext(wikitext).splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        heading = HEADING.match(line)
        if heading:
            flush()
            blocks.append(Block("heading", _inlines(heading.group(2)), len(heading.group(1)) - 1))
        elif line.startswith(("*", "#", ";", ":")):
            flush()
            blocks.append(Block("list_item", _inlines(line.lstrip("*#;: ").strip())))
        else:
            paragraph.append(line)
    flush()
    return Article(page_id, title, tuple(blocks), media=media)
