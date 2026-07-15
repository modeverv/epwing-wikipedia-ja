"""Math rendering failure fallback (TASK-N007, ARCHITECTURE.md 15.7 step 5).

Ties TASK-N003's renderer, TASK-N004's cache, and TASK-N005's raster
conversion into a single call that never raises: a failure anywhere in
that pipeline (unsupported TeX syntax, a PNG decode error, ...) falls
back to the caller-supplied plain text -- TASK-N001's text alternative,
or the TeX source itself when no text alternative was captured --
together with a `MATH_RENDER_FAILED` diagnostic recording why, so one
article's one bad formula can't fail the whole build (ARCHITECTURE.md
3.5's failure-isolation policy).
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.math_cache import MathCache
from wikiepwing.normalize.math_raster import MathRasterError, convert_png_to_bmp
from wikiepwing.normalize.math_renderer import MathRenderError, render_math_to_image

_MATH_RENDER_FAILED_CODE = "MATH_RENDER_FAILED"


@dataclass(frozen=True, slots=True)
class MathRenderOutcome:
    """Either a successfully rendered graphic's bytes, or a text fallback."""

    bitmap: bytes | None
    fallback_text: str | None
    diagnostics: tuple[Diagnostic, ...]


def render_math_with_fallback(
    tex_source: str,
    fallback_text: str,
    *,
    cache: MathCache,
    cache_key: str | None,
    font_size: int = 16,
) -> MathRenderOutcome:
    """Render `tex_source` to a BMP graphic, falling back to `fallback_text` on failure."""
    try:
        png_bytes = cache.get_or_render(
            cache_key,
            image_format="png",
            render=lambda: render_math_to_image(
                tex_source, image_format="png", font_size=font_size
            ),
        )
        bitmap = convert_png_to_bmp(png_bytes)
    except (MathRenderError, MathRasterError) as error:
        return MathRenderOutcome(
            bitmap=None,
            fallback_text=fallback_text,
            diagnostics=(_fallback_diagnostic(tex_source, error),),
        )
    return MathRenderOutcome(bitmap=bitmap, fallback_text=None, diagnostics=())


def _fallback_diagnostic(tex_source: str, error: Exception) -> Diagnostic:
    return Diagnostic(
        code=_MATH_RENDER_FAILED_CODE,
        severity="warning",
        stage="normalize_math_fallback",
        page_id=None,
        title=None,
        message=f"cannot render math source {tex_source!r}, falling back to text: {error}",
        source_path=None,
        source_excerpt=None,
        details={},
    )
