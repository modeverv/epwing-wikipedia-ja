"""Canonical JSON codec for Article (PLAN.md Phase 5 "JSON debug codec"/"schema version").

Wraps `Article.payload()`/`parse_article()` with a `schema_version` envelope
(matching DATA_CONTRACTS.md's Article JSON example) and serializes it with a
fixed key order, fixed separators, and no ASCII-escaping so identical Article
content always produces byte-identical output. Computing a hash on top of
these canonical bytes is TASK-F008's concern, not this module's.
"""

from __future__ import annotations

import json

from wikiepwing.model.article import Article, ArticleError, parse_article

CURRENT_SCHEMA_VERSION = 1


class CanonicalCodecError(ValueError):
    """Raised when canonical Article JSON cannot be encoded or decoded safely."""


def encode_article(article: Article) -> bytes:
    """Return the deterministic canonical JSON bytes for one Article."""
    envelope: dict[str, object] = {"schema_version": CURRENT_SCHEMA_VERSION}
    envelope.update(article.payload())
    return json.dumps(
        envelope,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def decode_article(data: bytes) -> Article:
    """Parse canonical JSON bytes back into an Article (the inverse of `encode_article`)."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CanonicalCodecError("canonical article bytes are not valid UTF-8") from error
    try:
        envelope = json.loads(text)
    except json.JSONDecodeError as error:
        raise CanonicalCodecError(f"canonical article bytes are not valid JSON: {error}") from error
    if not isinstance(envelope, dict):
        raise CanonicalCodecError("canonical article envelope must be a JSON object")

    schema_version = envelope.get("schema_version")
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise CanonicalCodecError(f"unsupported schema_version: {schema_version!r}")

    fields = {key: value for key, value in envelope.items() if key != "schema_version"}
    try:
        return parse_article(fields)
    except ArticleError as error:
        raise CanonicalCodecError(f"canonical article envelope is invalid: {error}") from error
