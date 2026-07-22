"""Conservative reading extraction from a normalized article lead."""

from __future__ import annotations

import re

from wikiepwing.model.article import Article
from wikiepwing.model.blocks import HeadingBlock, ParagraphBlock
from wikiepwing.model.inline import Inline

_PARENTHETICAL_SUFFIX = re.compile(r"\s*[（(][^（）()]+[）)]$")
_READING_PART = re.compile(r"^[ぁ-ゖァ-ヶー]+$")
_REFERENCE_MARKER = re.compile(r"\[[0-9]+\]")


def reading_for_article(article: Article) -> str | None:
    """Return the first explicit kana reading attached to the lead title.

    Wikipedia lead prose commonly uses ``『Title』（reading）`` or
    ``Title（reading、...）``. Only that explicit, local evidence is accepted;
    this function never guesses a kanji reading and never scans past the first
    section heading.
    """
    base_title = _PARENTHETICAL_SUFFIX.sub("", article.title).strip()
    if not base_title:
        return None
    quoted_title = rf"[『「]?{re.escape(base_title)}[』」]?"
    pattern = re.compile(rf"{quoted_title}\s*[（(]([^）)]{{1,128}})[）)]")
    for block in article.blocks:
        if isinstance(block, HeadingBlock):
            break
        if not isinstance(block, ParagraphBlock):
            continue
        text = _flatten_inlines(block.inlines)
        for match in pattern.finditer(text):
            reading = _first_reading_part(match.group(1))
            if reading is not None:
                return reading
    return None


def _first_reading_part(value: str) -> str | None:
    cleaned = _REFERENCE_MARKER.sub("", value)
    for part in re.split(r"[、,，/／]", cleaned):
        candidate = part.strip()
        if candidate and _READING_PART.fullmatch(candidate):
            return _katakana_to_hiragana(candidate)
    return None


def _katakana_to_hiragana(value: str) -> str:
    converted: list[str] = []
    for character in value:
        code_point = ord(character)
        if 0x30A1 <= code_point <= 0x30F6:
            converted.append(chr(code_point - 0x60))
        else:
            converted.append(character)
    return "".join(converted)


def _flatten_inlines(inlines: tuple[Inline, ...]) -> str:
    parts: list[str] = []
    for inline in inlines:
        value = getattr(inline, "value", None)
        if isinstance(value, str):
            parts.append(value)
            continue
        nested = getattr(inline, "inlines", None)
        if nested is not None:
            parts.append(_flatten_inlines(nested))
            continue
        label = getattr(inline, "label", None)
        if label is not None:
            parts.append(_flatten_inlines(label))
            continue
        fallback = getattr(inline, "fallback_text", None)
        if isinstance(fallback, str):
            parts.append(fallback)
    return "".join(parts)
