from __future__ import annotations

from pathlib import Path

from wikiepwing.normalize.math_cache import MathCache
from wikiepwing.normalize.math_fallback import render_math_with_fallback


def test_successful_render_returns_bitmap_and_no_fallback(tmp_path: Path) -> None:
    cache = MathCache(tmp_path)

    outcome = render_math_with_fallback(
        "E=mc^2", "E=mc^2 (fallback)", cache=cache, cache_key="key1"
    )

    assert outcome.bitmap is not None
    assert outcome.bitmap.startswith(b"BM")
    assert outcome.fallback_text is None
    assert outcome.diagnostics == ()


def test_render_failure_falls_back_to_text_with_diagnostic(tmp_path: Path) -> None:
    cache = MathCache(tmp_path)

    outcome = render_math_with_fallback(
        r"\notarealcommand{x}", "plain text fallback", cache=cache, cache_key="key1"
    )

    assert outcome.bitmap is None
    assert outcome.fallback_text == "plain text fallback"
    assert len(outcome.diagnostics) == 1
    assert outcome.diagnostics[0].code == "MATH_RENDER_FAILED"
    assert outcome.diagnostics[0].severity == "warning"


def test_successful_render_is_cached_and_not_re_rendered(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import wikiepwing.normalize.math_fallback as math_fallback_module

    calls = []
    original = math_fallback_module.render_math_to_image

    def counting_render(*args, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(math_fallback_module, "render_math_to_image", counting_render)
    cache = MathCache(tmp_path)

    first = render_math_with_fallback("E=mc^2", "fallback", cache=cache, cache_key="key1")
    second = render_math_with_fallback("E=mc^2", "fallback", cache=cache, cache_key="key1")

    assert first.bitmap == second.bitmap
    assert len(calls) == 1


def test_none_cache_key_always_renders_fresh(tmp_path: Path) -> None:
    cache = MathCache(tmp_path)

    outcome = render_math_with_fallback("E=mc^2", "fallback", cache=cache, cache_key=None)

    assert outcome.bitmap is not None
    assert outcome.fallback_text is None
