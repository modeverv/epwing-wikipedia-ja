"""External link policy (TASK-H003, ARCHITECTURE.md 12.5: "外部サイトへのリンクは
plain URLまたは注記として残します").

Applied to any href TASK-H001's `parse_internal_url` decided is *not* an
internal wiki link. Only `http`/`https` (and protocol-relative `//host/...`,
treated as `https`) schemes become a real `ExternalLinkInline`; anything else
(`javascript:`, `data:`, unscoped relative paths, etc.) is not safe to carry
through as a clickable link, so only the label is kept -- content is never
silently dropped.
"""

from __future__ import annotations

import urllib.parse
from typing import Literal

from wikiepwing.model.inline import ExternalLinkInline, Inline

ExternalLinkPolicy = Literal["plain-text"]
_POLICIES = ("plain-text",)

_SAFE_SCHEMES = frozenset({"http", "https"})


class ExternalLinkPolicyError(ValueError):
    """Raised when an external link policy value is invalid."""


def apply_external_link_policy(
    label: tuple[Inline, ...], url: str, policy: str
) -> tuple[Inline, ...]:
    """Return the Inline(s) representing one external-site href under `policy`."""
    if policy not in _POLICIES:
        raise ExternalLinkPolicyError(f"policy must be one of {_POLICIES}: {policy!r}")

    if _is_safe_url(url):
        resolved_url = f"https:{url}" if url.startswith("//") else url
        return (ExternalLinkInline(label=label, url=resolved_url),)

    return label


def _is_safe_url(url: str) -> bool:
    if url.startswith("//"):
        return True
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return parsed.scheme.lower() in _SAFE_SCHEMES and bool(parsed.netloc)
