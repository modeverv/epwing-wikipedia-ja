from __future__ import annotations

import pytest

from wikiepwing.normalize.math_renderer import MathRenderError, render_math_to_image


def test_renders_simple_formula_to_svg() -> None:
    result = render_math_to_image("E=mc^2", image_format="svg")

    assert result.startswith(b"<?xml")
    assert b"<svg" in result


def test_renders_simple_formula_to_png() -> None:
    result = render_math_to_image("E=mc^2", image_format="png")

    assert result.startswith(b"\x89PNG\r\n\x1a\n")


def test_default_format_is_svg() -> None:
    result = render_math_to_image("E=mc^2")

    assert result.startswith(b"<?xml")


def test_different_formulas_render_different_bytes() -> None:
    a = render_math_to_image("E=mc^2")
    b = render_math_to_image("a^2+b^2=c^2")

    assert a != b


def test_svg_rendering_is_deterministic_for_the_same_formula() -> None:
    # matplotlib's SVG writer otherwise embeds a wall-clock timestamp and a
    # per-process glyph-id salt, so this is the regression test for both
    # fixes (fixed svg.hashsalt, stripped <dc:date>).
    first = render_math_to_image("E=mc^2", image_format="svg")
    second = render_math_to_image("E=mc^2", image_format="svg")

    assert first == second


def test_png_rendering_is_deterministic_for_the_same_formula() -> None:
    first = render_math_to_image("E=mc^2", image_format="png")
    second = render_math_to_image("E=mc^2", image_format="png")

    assert first == second


def test_empty_source_raises_math_render_error() -> None:
    with pytest.raises(MathRenderError, match="empty"):
        render_math_to_image("")


def test_whitespace_only_source_raises_math_render_error() -> None:
    with pytest.raises(MathRenderError):
        render_math_to_image("   ")


def test_unsupported_macro_raises_math_render_error_without_crashing() -> None:
    with pytest.raises(MathRenderError, match="cannot render math source"):
        render_math_to_image(r"\notarealcommand{x}")


def test_render_error_after_failure_does_not_prevent_later_renders() -> None:
    with pytest.raises(MathRenderError):
        render_math_to_image(r"\notarealcommand{x}")

    # A failed render must not leave the renderer in a broken state for
    # subsequent, valid formulas (ARCHITECTURE.md 3.5: isolate failures).
    result = render_math_to_image("E=mc^2")
    assert result.startswith(b"<?xml")
