from __future__ import annotations

from pathlib import Path

from wikiepwing.normalize.math_cache import MathCache


def test_cache_miss_calls_render_and_returns_its_result(tmp_path: Path) -> None:
    cache = MathCache(tmp_path)
    calls = []

    result = cache.get_or_render(
        "key1", image_format="svg", render=lambda: calls.append(1) or b"rendered"
    )

    assert result == b"rendered"
    assert len(calls) == 1


def test_cache_hit_does_not_call_render_again(tmp_path: Path) -> None:
    cache = MathCache(tmp_path)
    calls = []

    def render() -> bytes:
        calls.append(1)
        return b"rendered"

    first = cache.get_or_render("key1", image_format="svg", render=render)
    second = cache.get_or_render("key1", image_format="svg", render=render)

    assert first == second == b"rendered"
    assert len(calls) == 1


def test_none_cache_key_always_renders_fresh(tmp_path: Path) -> None:
    cache = MathCache(tmp_path)
    calls = []

    def render() -> bytes:
        calls.append(1)
        return b"rendered"

    cache.get_or_render(None, image_format="svg", render=render)
    cache.get_or_render(None, image_format="svg", render=render)

    assert len(calls) == 2


def test_different_cache_keys_are_stored_independently(tmp_path: Path) -> None:
    cache = MathCache(tmp_path)

    a = cache.get_or_render("key1", image_format="svg", render=lambda: b"a")
    b = cache.get_or_render("key2", image_format="svg", render=lambda: b"b")

    assert a == b"a"
    assert b == b"b"


def test_different_image_formats_are_stored_independently(tmp_path: Path) -> None:
    cache = MathCache(tmp_path)

    svg = cache.get_or_render("key1", image_format="svg", render=lambda: b"svg-bytes")
    png = cache.get_or_render("key1", image_format="png", render=lambda: b"png-bytes")

    assert svg == b"svg-bytes"
    assert png == b"png-bytes"


def test_cache_creates_missing_directory(tmp_path: Path) -> None:
    cache = MathCache(tmp_path / "nested" / "math-cache")

    result = cache.get_or_render("key1", image_format="svg", render=lambda: b"rendered")

    assert result == b"rendered"


def test_bumping_cache_version_invalidates_old_entries(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import wikiepwing.normalize.math_cache as math_cache_module

    cache = MathCache(tmp_path)
    calls = []

    def render() -> bytes:
        calls.append(1)
        return b"rendered"

    cache.get_or_render("key1", image_format="svg", render=render)
    monkeypatch.setattr(math_cache_module, "MATH_CACHE_VERSION", 2)
    cache.get_or_render("key1", image_format="svg", render=render)

    assert len(calls) == 2
