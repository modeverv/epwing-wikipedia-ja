from __future__ import annotations

from pathlib import Path

from wikiepwing.media.cache import MediaCache, compute_content_hash


def test_compute_content_hash_is_sha256_hex_digest() -> None:
    import hashlib

    content = b"some bytes"

    assert compute_content_hash(content) == hashlib.sha256(content).hexdigest()


def test_compute_content_hash_differs_for_different_content() -> None:
    assert compute_content_hash(b"a") != compute_content_hash(b"b")


def test_cache_miss_calls_convert_and_returns_its_result(tmp_path: Path) -> None:
    cache = MediaCache(tmp_path)
    calls = []

    result = cache.get_or_convert("hash1", convert=lambda: calls.append(1) or b"converted")

    assert result == b"converted"
    assert len(calls) == 1


def test_cache_hit_does_not_call_convert_again(tmp_path: Path) -> None:
    cache = MediaCache(tmp_path)
    calls = []

    def convert() -> bytes:
        calls.append(1)
        return b"converted"

    first = cache.get_or_convert("hash1", convert=convert)
    second = cache.get_or_convert("hash1", convert=convert)

    assert first == second == b"converted"
    assert len(calls) == 1


def test_different_content_hashes_are_stored_independently(tmp_path: Path) -> None:
    cache = MediaCache(tmp_path)

    a = cache.get_or_convert("hash1", convert=lambda: b"a")
    b = cache.get_or_convert("hash2", convert=lambda: b"b")

    assert a == b"a"
    assert b == b"b"


def test_cache_creates_missing_directory(tmp_path: Path) -> None:
    cache = MediaCache(tmp_path / "nested" / "media-cache")

    result = cache.get_or_convert("hash1", convert=lambda: b"converted")

    assert result == b"converted"


def test_bumping_cache_version_invalidates_old_entries(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import wikiepwing.media.cache as media_cache_module

    cache = MediaCache(tmp_path)
    calls = []

    def convert() -> bytes:
        calls.append(1)
        return b"converted"

    cache.get_or_convert("hash1", convert=convert)
    monkeypatch.setattr(media_cache_module, "MEDIA_CACHE_VERSION", 2)
    cache.get_or_convert("hash1", convert=convert)

    assert len(calls) == 2
