"""Resolve every internal link nested in an Article against raw.sqlite3."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from typing import cast

from wikiepwing.links.resolver import ResolvedLink, resolve_internal_link
from wikiepwing.links.url_parser import ParsedInternalUrl, parse_internal_url
from wikiepwing.model.article import Article, parse_article


def resolve_article_links(
    article: Article,
    connection: sqlite3.Connection,
    *,
    project_base_urls: tuple[str, ...],
    resolution_cache: dict[str, ResolvedLink] | None = None,
) -> Article:
    """Return ``article`` with nested link targets resolved deterministically."""
    payload = article.payload()
    return parse_article(_resolve_value(payload, connection, project_base_urls, resolution_cache))


def _resolve_value(
    value: object,
    connection: sqlite3.Connection,
    project_base_urls: tuple[str, ...],
    resolution_cache: dict[str, ResolvedLink] | None,
) -> object:
    if isinstance(value, list):
        return [
            _resolve_value(item, connection, project_base_urls, resolution_cache) for item in value
        ]
    if not isinstance(value, dict):
        return value

    fields = cast(dict[str, object], value)
    kind = fields.get("type")
    if kind == "internal_link":
        return _resolve_internal_payload(fields, connection, resolution_cache)
    if kind == "external_link":
        converted = _convert_project_link(fields, connection, project_base_urls, resolution_cache)
        if converted is not None:
            return converted
    return {
        key: _resolve_value(item, connection, project_base_urls, resolution_cache)
        for key, item in fields.items()
    }


def _resolve_internal_payload(
    fields: dict[str, object],
    connection: sqlite3.Connection,
    resolution_cache: dict[str, ResolvedLink] | None,
) -> dict[str, object]:
    if fields.get("resolution") == "externalized":
        return fields
    title = fields["target_title"]
    fragment = fields.get("target_fragment")
    assert isinstance(title, str)
    assert fragment is None or isinstance(fragment, str)
    resolved = _resolve_cached(title, fragment, connection, resolution_cache)
    return {
        **fields,
        "target_normalized_title": resolved.target_normalized_title,
        "target_page_id": resolved.target_page_id,
        "resolution": resolved.resolution,
    }


def _convert_project_link(
    fields: dict[str, object],
    connection: sqlite3.Connection,
    project_base_urls: tuple[str, ...],
    resolution_cache: dict[str, ResolvedLink] | None,
) -> dict[str, object] | None:
    url = fields["url"]
    assert isinstance(url, str)
    parsed = parse_internal_url(url, project_base_urls=project_base_urls)
    if parsed is None:
        return None
    if parsed.namespace is None:
        resolved = _resolve_cached(parsed.title, parsed.fragment, connection, resolution_cache)
    else:
        resolved = resolve_internal_link(parsed, connection)
    return {
        "type": "internal_link",
        "label": fields["label"],
        "target_title": resolved.target_title,
        "target_normalized_title": resolved.target_normalized_title,
        "target_fragment": resolved.target_fragment,
        "target_page_id": resolved.target_page_id,
        "resolution": resolved.resolution,
    }


def _resolve_cached(
    title: str,
    fragment: str | None,
    connection: sqlite3.Connection,
    resolution_cache: dict[str, ResolvedLink] | None,
) -> ResolvedLink:
    cached = resolution_cache.get(title) if resolution_cache is not None else None
    if cached is None:
        cached = resolve_internal_link(
            ParsedInternalUrl(namespace=None, title=title, fragment=None), connection
        )
        if resolution_cache is not None:
            resolution_cache[title] = cached
    return replace(cached, target_fragment=fragment)
