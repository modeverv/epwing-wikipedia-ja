from __future__ import annotations

from wikiepwing.model.article import MediaReference
from wikiepwing.normalize.media_selection import select_media


def _media(url: str, role: str, **overrides: object) -> MediaReference:
    defaults: dict[str, object] = {
        "media_id": url,
        "source_url": url,
        "source_name": None,
        "alt_text": None,
        "caption": None,
        "role": role,
        "source_width": None,
        "source_height": None,
    }
    defaults.update(overrides)
    return MediaReference(**defaults)  # type: ignore[arg-type]


def test_empty_input_returns_empty_tuple() -> None:
    assert select_media(()) == ()


def test_icons_are_excluded() -> None:
    icon = _media("icon.png", "icon")
    body = _media("body.png", "body")

    result = select_media((icon, body))

    assert result == (body,)


def test_duplicate_source_urls_keep_only_the_first() -> None:
    first = _media("a.png", "body")
    duplicate = _media("a.png", "lead")

    result = select_media((first, duplicate))

    assert result == (first,)


def test_orders_by_role_priority() -> None:
    body = _media("body.png", "body")
    lead = _media("lead.png", "lead")
    infobox = _media("infobox.png", "infobox")
    main = _media("main.png", "main")

    result = select_media((body, lead, infobox, main))

    assert result == (main, infobox, lead, body)


def test_unknown_role_sorts_after_body() -> None:
    body = _media("body.png", "body")
    unknown = _media("unknown.png", "unknown")

    result = select_media((unknown, body))

    assert result == (body, unknown)


def test_stable_sort_preserves_dom_order_within_the_same_role() -> None:
    first_body = _media("first.png", "body")
    second_body = _media("second.png", "body")

    result = select_media((first_body, second_body))

    assert result == (first_body, second_body)


def test_icon_exclusion_and_deduplication_and_ordering_combined() -> None:
    icon = _media("icon.png", "icon")
    lead = _media("lead.png", "lead")
    main = _media("main.png", "main")
    duplicate_main = _media("main.png", "main")

    result = select_media((icon, lead, main, duplicate_main))

    assert result == (main, lead)
