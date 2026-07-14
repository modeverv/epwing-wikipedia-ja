from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from wikiepwing.model.article import Article
from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.canonical import (
    CURRENT_SCHEMA_VERSION,
    CanonicalCodecError,
    decode_article,
    encode_article,
)
from wikiepwing.model.inline import TextInline


def _make_article(**overrides: object) -> Article:
    defaults: dict[str, object] = {
        "page_id": 123,
        "revision_id": 456,
        "title": "Emacs",
        "normalized_title": "Emacs",
        "source_url": "https://ja.wikipedia.org/wiki/Emacs",
        "source_date_modified": datetime(2026, 1, 1, tzinfo=UTC),
        "abstract": None,
        "blocks": (ParagraphBlock(inlines=(TextInline("hello"),)),),
        "aliases": (),
        "categories": (),
        "media": (),
        "diagnostics": (),
        "source_license_ids": ("CC-BY-SA-3.0",),
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def test_encode_decode_article_round_trips() -> None:
    article = _make_article()

    restored = decode_article(encode_article(article))

    assert restored == article


def test_encode_article_is_deterministic() -> None:
    article = _make_article()

    first = encode_article(article)
    second = encode_article(article)

    assert first == second


def test_encode_article_embeds_schema_version_envelope() -> None:
    article = _make_article()

    envelope = json.loads(encode_article(article))

    assert envelope["schema_version"] == CURRENT_SCHEMA_VERSION
    assert envelope["page_id"] == 123
    assert envelope["title"] == "Emacs"


def test_encode_article_output_has_sorted_keys_and_compact_separators() -> None:
    article = _make_article()

    text = encode_article(article).decode("utf-8")

    assert " " not in text
    top_level_keys = list(json.loads(text).keys())
    assert top_level_keys == sorted(top_level_keys)


def test_decode_article_rejects_wrong_schema_version() -> None:
    article = _make_article()
    envelope = json.loads(encode_article(article))
    envelope["schema_version"] = 2
    data = json.dumps(envelope).encode("utf-8")

    with pytest.raises(CanonicalCodecError, match="schema_version"):
        decode_article(data)


def test_decode_article_rejects_missing_schema_version() -> None:
    article = _make_article()
    envelope = json.loads(encode_article(article))
    del envelope["schema_version"]
    data = json.dumps(envelope).encode("utf-8")

    with pytest.raises(CanonicalCodecError, match="schema_version"):
        decode_article(data)


def test_decode_article_rejects_invalid_json() -> None:
    with pytest.raises(CanonicalCodecError, match="valid JSON"):
        decode_article(b"{not json")


def test_decode_article_rejects_non_object_envelope() -> None:
    with pytest.raises(CanonicalCodecError, match="JSON object"):
        decode_article(b"[1, 2, 3]")


def test_decode_article_rejects_invalid_utf8() -> None:
    with pytest.raises(CanonicalCodecError, match="UTF-8"):
        decode_article(b"\xff\xfe")


def test_decode_article_rejects_invalid_article_fields() -> None:
    article = _make_article()
    envelope = json.loads(encode_article(article))
    envelope["title"] = ""
    data = json.dumps(envelope).encode("utf-8")

    with pytest.raises(CanonicalCodecError, match="invalid"):
        decode_article(data)
