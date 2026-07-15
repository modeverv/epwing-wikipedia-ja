from __future__ import annotations

from wikiepwing.media.dedup import HashedMedia, deduplicate_media
from wikiepwing.model.article import MediaReference


def _media(url: str, **overrides: object) -> MediaReference:
    defaults: dict[str, object] = {
        "media_id": url,
        "source_url": url,
        "source_name": None,
        "alt_text": None,
        "caption": None,
        "role": "body",
        "source_width": None,
        "source_height": None,
    }
    defaults.update(overrides)
    return MediaReference(**defaults)  # type: ignore[arg-type]


def test_empty_input_returns_empty_tuple() -> None:
    assert deduplicate_media(()) == ()


def test_distinct_content_hashes_are_all_kept() -> None:
    first = HashedMedia(media=_media("a.png"), content_hash="hash1")
    second = HashedMedia(media=_media("b.png"), content_hash="hash2")

    result = deduplicate_media((first, second))

    assert result == (first.media, second.media)


def test_same_content_hash_with_different_urls_keeps_only_the_first() -> None:
    first = HashedMedia(media=_media("thumb-100px.png"), content_hash="same-hash")
    second = HashedMedia(media=_media("thumb-200px.png"), content_hash="same-hash")

    result = deduplicate_media((first, second))

    assert result == (first.media,)


def test_preserves_input_order() -> None:
    first = HashedMedia(media=_media("z.png"), content_hash="hash-z")
    second = HashedMedia(media=_media("a.png"), content_hash="hash-a")

    result = deduplicate_media((first, second))

    assert result == (first.media, second.media)


def test_three_way_duplicate_keeps_only_the_first() -> None:
    entries = tuple(HashedMedia(media=_media(f"{i}.png"), content_hash="dup") for i in range(3))

    result = deduplicate_media(entries)

    assert result == (entries[0].media,)
