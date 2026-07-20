"""Exact and redirect-title index construction."""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.mediawiki.redirects import normalize_title


@dataclass(frozen=True, slots=True)
class HeadwordIndex:
    entries: tuple[tuple[str, str], ...]
    collisions: tuple[str, ...]


def build_headword_index(
    titles: tuple[str, ...], aliases: tuple[tuple[str, str], ...]
) -> HeadwordIndex:
    """Build normalized lookup keys without silently overwriting collisions."""
    values: dict[str, str] = {}
    collisions: list[str] = []
    for title in sorted(titles):
        key = normalize_title(title)
        if key in values and values[key] != title:
            collisions.append(key)
        else:
            values[key] = title
    for alias, target in sorted(aliases):
        key = normalize_title(alias)
        if key in values and values[key] != target:
            collisions.append(key)
        else:
            values[key] = target
    return HeadwordIndex(tuple(sorted(values.items())), tuple(sorted(set(collisions))))
