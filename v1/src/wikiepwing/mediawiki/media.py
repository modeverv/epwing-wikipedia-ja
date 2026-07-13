"""Media-reference extraction from conservative Wikitext parsing."""

from __future__ import annotations

import re

from wikiepwing.model.article import MediaReference

FILE_LINK = re.compile(r"\[\[\s*(File|Image|ファイル|画像)\s*:\s*([^\]|]+)(.*?)\]\]", re.IGNORECASE)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
INFOBOX_IMAGE = re.compile(
    r"^[^\S\r\n]*\|[^\S\r\n]*(?:画像|image|logo|ロゴ)[^\S\r\n]*=[^\S\r\n]*(?P<value>[^\r\n]*)$",
    re.IGNORECASE | re.MULTILINE,
)

_FILE_OPTIONS = {
    "thumb",
    "thumbnail",
    "frame",
    "frameless",
    "right",
    "left",
    "center",
    "none",
    "upright",
    "border",
}


def _clean_file_name(value: str) -> str:
    name = value.strip().replace("_", " ")
    if any(marker in name for marker in ("[[", "]]", "{{", "}}", "<!--", "-->", "|")):
        return ""
    for prefix in ("File:", "Image:", "ファイル:", "画像:"):
        if name.casefold().startswith(prefix.casefold()):
            name = name[len(prefix) :].strip()
            break
    if "\x00" in name or name in {"", ".", ".."}:
        return ""
    return name


def _caption(parts: list[str]) -> str:
    for part in reversed(parts):
        text = part.strip()
        if not text or "=" in text:
            continue
        if text.casefold() in _FILE_OPTIONS:
            continue
        if re.fullmatch(r"\d+(?:x\d+)?px", text.casefold()):
            continue
        if "[[" in text or "]]" in text or "{{" in text or "}}" in text:
            continue
        return text
    return ""


def _dedupe(media: list[MediaReference]) -> tuple[MediaReference, ...]:
    seen: set[str] = set()
    result: list[MediaReference] = []
    for item in media:
        key = item.file_name.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return tuple(result)


def extract_media_references(wikitext: str) -> tuple[MediaReference, ...]:
    """Return deterministic image candidates without resolving remote metadata."""
    wikitext = COMMENT.sub("", wikitext)
    media: list[MediaReference] = []

    for match in INFOBOX_IMAGE.finditer(wikitext):
        file_name = _clean_file_name(match.group("value"))
        if file_name:
            media.append(MediaReference(file_name, source="infobox"))

    for match in FILE_LINK.finditer(wikitext):
        file_name = _clean_file_name(match.group(2))
        if not file_name:
            continue
        parts = [part for part in match.group(3).split("|") if part]
        media.append(MediaReference(file_name, _caption(parts), "article"))

    return _dedupe(media)


def strip_file_links(wikitext: str) -> str:
    """Remove image markup from prose after media extraction."""
    return FILE_LINK.sub("", wikitext)
