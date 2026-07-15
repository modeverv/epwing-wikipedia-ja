from __future__ import annotations

from wikiepwing.model.article import MediaReference
from wikiepwing.normalize.media_role import classify_media_role, with_classified_role


def _media(**overrides: object) -> MediaReference:
    defaults: dict[str, object] = {
        "media_id": "https://example.org/a.png",
        "source_url": "https://example.org/a.png",
        "source_name": "a.png",
        "alt_text": None,
        "caption": None,
        "role": "unknown",
        "source_width": 400,
        "source_height": 300,
    }
    defaults.update(overrides)
    return MediaReference(**defaults)  # type: ignore[arg-type]


def test_main_role_is_never_overridden() -> None:
    media = _media(role="main", source_width=10, source_height=10)

    role = classify_media_role(media, infobox_source_urls={media.source_url}, is_lead=True)

    assert role == "main"


def test_small_dimensions_classify_as_icon() -> None:
    media = _media(source_width=16, source_height=16)

    role = classify_media_role(media)

    assert role == "icon"


def test_icon_classification_takes_priority_over_infobox() -> None:
    media = _media(source_width=16, source_height=16)

    role = classify_media_role(media, infobox_source_urls={media.source_url})

    assert role == "icon"


def test_infobox_source_url_classifies_as_infobox() -> None:
    media = _media()

    role = classify_media_role(media, infobox_source_urls={media.source_url})

    assert role == "infobox"


def test_lead_flag_classifies_as_lead_when_not_icon_or_infobox() -> None:
    media = _media()

    role = classify_media_role(media, is_lead=True)

    assert role == "lead"


def test_infobox_takes_priority_over_lead() -> None:
    media = _media()

    role = classify_media_role(media, infobox_source_urls={media.source_url}, is_lead=True)

    assert role == "infobox"


def test_default_classification_is_body() -> None:
    media = _media()

    role = classify_media_role(media)

    assert role == "body"


def test_unknown_dimensions_do_not_classify_as_icon() -> None:
    media = _media(source_width=None, source_height=None)

    role = classify_media_role(media)

    assert role == "body"


def test_partially_known_dimensions_do_not_classify_as_icon() -> None:
    media = _media(source_width=16, source_height=None)

    role = classify_media_role(media)

    assert role == "body"


def test_with_classified_role_preserves_other_fields() -> None:
    media = _media()

    classified = with_classified_role(media, is_lead=True)

    assert classified.role == "lead"
    assert classified.source_url == media.source_url
    assert classified.source_name == media.source_name
    assert classified.alt_text == media.alt_text
    assert classified.caption == media.caption
    assert classified.source_width == media.source_width
    assert classified.source_height == media.source_height
