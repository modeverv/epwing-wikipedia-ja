from __future__ import annotations

import pytest

from wikiepwing.media.attribution import (
    AttributionError,
    MediaAttribution,
    is_licensed,
    parse_media_attribution,
)


def test_round_trips_a_fully_populated_attribution() -> None:
    attribution = MediaAttribution(
        source_page_url="https://commons.wikimedia.org/wiki/File:Example.png",
        author="Jane Doe",
        license_identifier="CC-BY-SA-4.0",
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",
    )

    restored = parse_media_attribution(attribution.payload())

    assert restored == attribution


def test_payload_uses_data_contracts_field_names() -> None:
    attribution = MediaAttribution(
        source_page_url="https://example.org/file",
        author="A",
        license_identifier="CC0-1.0",
        license_url="https://example.org/license",
    )

    assert attribution.payload() == {
        "source_page_url": "https://example.org/file",
        "author": "A",
        "license_identifier": "CC0-1.0",
        "license_url": "https://example.org/license",
    }


def test_all_fields_are_nullable() -> None:
    attribution = MediaAttribution(
        source_page_url=None, author=None, license_identifier=None, license_url=None
    )

    restored = parse_media_attribution(attribution.payload())

    assert restored == attribution


def test_is_licensed_true_when_license_identifier_present() -> None:
    attribution = MediaAttribution(
        source_page_url=None, author=None, license_identifier="CC0-1.0", license_url=None
    )

    assert is_licensed(attribution) is True


def test_is_licensed_false_when_license_identifier_missing() -> None:
    attribution = MediaAttribution(
        source_page_url=None, author=None, license_identifier=None, license_url=None
    )

    assert is_licensed(attribution) is False


def test_is_licensed_false_when_attribution_is_none() -> None:
    assert is_licensed(None) is False


def test_parse_rejects_non_object() -> None:
    with pytest.raises(AttributionError, match="JSON object"):
        parse_media_attribution(["not", "an", "object"])


def test_parse_rejects_non_string_field() -> None:
    with pytest.raises(AttributionError, match="author"):
        parse_media_attribution(
            {
                "source_page_url": None,
                "author": 123,
                "license_identifier": None,
                "license_url": None,
            }
        )
