"""Internal link URL parsing (TASK-H001, ARCHITECTURE.md 12.5 steps 1-4).

Handles the three URL shapes ARCHITECTURE.md 12.5 lists as examples:
`/wiki/Title` (site-relative), a full URL matching one of the configured
project base URLs, and `./Title` (document-relative). Page ID resolution
(step 6, TASK-H002), redirect handling (step 7), and EPWING entry ID
conversion (step 8) are separate tasks. Anything that isn't one of these
shapes is treated as an external link (returns `None`), per 12.5's
"外部サイトへのリンクはplain URLまたは注記として残します".
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass

_KNOWN_NAMESPACES = frozenset(
    {
        "Category",
        "Template",
        "File",
        "Talk",
        "User",
        "Wikipedia",
        "Help",
        "Portal",
        "Module",
        "MediaWiki",
        "Special",
        "User talk",
        "Template talk",
        "Category talk",
        "File talk",
        "Wikipedia talk",
        "Help talk",
        "Portal talk",
        "Module talk",
        "MediaWiki talk",
        "カテゴリ",
        "テンプレート",
        "ファイル",
        "特別",
        "利用者",
        "利用者‐会話",
        "Wikipedia‐ノート",
        "ヘルプ",
        "ポータル",
        "モジュール",
    }
)


class UrlParseError(ValueError):
    """Raised when a URL cannot be parsed safely."""


@dataclass(frozen=True, slots=True)
class ParsedInternalUrl:
    """The namespace/title/fragment extracted from an internal wiki link URL."""

    namespace: str | None
    title: str
    fragment: str | None


def parse_internal_url(url: str, *, project_base_urls: tuple[str, ...]) -> ParsedInternalUrl | None:
    """Parse `url` as an internal wiki link, or return None if it is external."""
    if not url:
        raise UrlParseError("url must be a non-empty string")

    path = _extract_wiki_path(url, project_base_urls)
    if path is None:
        return None

    path, _, _query = path.partition("?")
    fragment: str | None = None
    if "#" in path:
        path, _, fragment_raw = path.partition("#")
        fragment = urllib.parse.unquote(fragment_raw) or None

    decoded = urllib.parse.unquote(path)
    raw_title = decoded.replace("_", " ").strip()
    if not raw_title:
        return None

    namespace, title = _split_namespace(raw_title)
    return ParsedInternalUrl(namespace=namespace, title=title, fragment=fragment)


def _extract_wiki_path(url: str, project_base_urls: tuple[str, ...]) -> str | None:
    if url.startswith("./"):
        return url[2:]
    if url.startswith("/wiki/"):
        return url[len("/wiki/") :]
    for base in project_base_urls:
        prefix = base.rstrip("/") + "/wiki/"
        if url.startswith(prefix):
            return url[len(prefix) :]
    return None


def _split_namespace(title: str) -> tuple[str | None, str]:
    if ":" not in title:
        return None, title
    prefix, _, rest = title.partition(":")
    if prefix in _KNOWN_NAMESPACES and rest:
        return prefix, rest
    return None, title
