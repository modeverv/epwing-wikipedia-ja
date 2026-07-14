"""Logical hash for Article (TASK-F008: order-independent sources -> deterministic output).

Builds on `wikiepwing.model.canonical`'s deterministic JSON serialization, but
first normalizes the ordering of collections whose extraction order is not
semantically meaningful (aliases/categories/media/diagnostics/source_license_ids),
so that two Articles with identical content that merely differ in the order
these were discovered hash identically. `blocks` (and everything nested under
them) is document-order-sensitive and is deliberately left untouched.
"""

from __future__ import annotations

import hashlib
import json
from typing import cast

from wikiepwing.model.article import Article

SCHEMA_VERSION = 1


def compute_logical_hash(article: Article) -> str:
    """Return the sha256 hex digest of the Article's order-normalized canonical form."""
    payload = article.payload()
    payload["categories"] = sorted(_as_str_list(payload["categories"]))
    payload["source_license_ids"] = sorted(_as_str_list(payload["source_license_ids"]))
    payload["aliases"] = sorted(
        _as_dict_list(payload["aliases"]),
        key=lambda alias: (
            cast(str, alias["title"]),
            cast(str, alias["source"]),
            cast(float, alias["confidence"]),
        ),
    )
    payload["media"] = sorted(
        _as_dict_list(payload["media"]),
        key=lambda media: cast(str, media["media_id"]),
    )
    payload["diagnostics"] = sorted(
        _as_dict_list(payload["diagnostics"]),
        key=lambda diagnostic: (
            cast(str, diagnostic["code"]),
            cast(int, diagnostic["page_id"]) if diagnostic["page_id"] is not None else -1,
            cast(str, diagnostic["title"]) or "",
            cast(str, diagnostic["message"]),
        ),
    )

    envelope: dict[str, object] = {"schema_version": SCHEMA_VERSION}
    envelope.update(payload)
    canonical_bytes = json.dumps(
        envelope,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def _as_str_list(value: object) -> list[str]:
    return cast(list[str], value)


def _as_dict_list(value: object) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], value)
