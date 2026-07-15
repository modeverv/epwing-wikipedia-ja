"""Math rendering to SVG/PNG (TASK-N003, ARCHITECTURE.md 15.7 "3. SVG/PNGへ安全にレンダリング").

Renders a TeX-like math source into an image using matplotlib's built-in
`mathtext` engine, running entirely in-process rather than shelling out to
an external LaTeX toolchain (a deliberate, user-approved scope decision:
no external rendering binary or Node.js toolchain exists anywhere in this
project, and mathtext needs no new system packages). `mathtext` supports a
useful subset of LaTeX math syntax, not the full macro set MediaWiki's
texvc extension allows -- an unsupported formula fails this one render
(raising `MathRenderError`) without needing to stop the rest of the
article's build, matching ARCHITECTURE.md 3.5's "機能不足は劣化表示し、
データ損失を記録する": the caller (TASK-N007 onward) catches this per
formula and falls back to the TeX/plain text ARCHITECTURE.md 15.7 already
requires saving (TASK-N001/N002).

matplotlib's SVG writer embeds a wall-clock `<dc:date>` timestamp and (by
default) a per-process-random glyph-id salt, so two renders of the exact
same formula would otherwise produce different bytes -- unacceptable for
this project's reproducible-build goal (ADR precedent: pinned Docker
snapshots, deterministic manifests). `svg.hashsalt` is fixed to a constant
so glyph ids are stable, and the timestamp is stripped from the output
after rendering.
"""

from __future__ import annotations

import io
import re
from typing import Literal

import matplotlib
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image

ImageFormat = Literal["svg", "png"]

_HASH_SALT = "wikiepwing-math-renderer"
_SVG_DATE_ELEMENT = re.compile(rb"<dc:date>.*?</dc:date>")


class MathRenderError(ValueError):
    """Raised when a math source cannot be rendered into an image."""


def render_math_to_image(
    tex_source: str, *, image_format: ImageFormat = "svg", font_size: int = 16
) -> bytes:
    """Render `tex_source` (a mathtext-compatible TeX-like string) to image bytes."""
    if not tex_source.strip():
        raise MathRenderError("tex_source must not be empty")

    buffer = io.BytesIO()
    try:
        with matplotlib.rc_context({"svg.hashsalt": _HASH_SALT}):
            math_to_image(
                f"${tex_source}$",
                buffer,
                format=image_format,
                prop=FontProperties(size=font_size),
            )
    except Exception as error:
        raise MathRenderError(f"cannot render math source {tex_source!r}: {error}") from error

    image_bytes = buffer.getvalue()
    if image_format == "svg":
        image_bytes = _SVG_DATE_ELEMENT.sub(b"<dc:date/>", image_bytes)
    return image_bytes
