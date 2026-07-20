"""Deterministic title normalization and redirect resolution."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

SPACE = re.compile(r"[ _\t\n\r]+")


def normalize_title(title: str) -> str:
    """Normalize compatibility characters and MediaWiki-equivalent whitespace."""
    normalized = SPACE.sub(" ", unicodedata.normalize("NFKC", title).strip())
    return normalized[:1].upper() + normalized[1:]


@dataclass(frozen=True, slots=True)
class RedirectResolution:
    source: str
    target: str | None
    diagnostic: str | None


def resolve_redirects(titles: set[str], redirects: dict[str, str]) -> list[RedirectResolution]:
    """Resolve each normalized redirect with explicit broken/cycle diagnostics."""
    result: list[RedirectResolution] = []
    normalized_titles = {normalize_title(title) for title in titles}
    normalized_redirects = {
        normalize_title(source): normalize_title(target) for source, target in redirects.items()
    }
    for source in sorted(normalized_redirects):
        seen: set[str] = set()
        current = source
        while current in normalized_redirects:
            if current in seen:
                result.append(RedirectResolution(source, None, "REDIRECT_CYCLE"))
                break
            seen.add(current)
            current = normalized_redirects[current]
        else:
            if current in normalized_titles:
                result.append(RedirectResolution(source, current, None))
            else:
                result.append(RedirectResolution(source, None, "REDIRECT_TARGET_MISSING"))
    return result
