"""Shared math source resolution for block/inline layout (TASK-N006, ARCHITECTURE.md 15.7).

Both `convert_block` (block-level `<math display="block">`) and
`convert_inline_nodes` (inline `<math>`) need the same "which source do
we actually have" decision that TASK-N002's `compute_math_cache_key`
already makes: prefer the TeX source, fall back to the text alternative,
and treat neither being present as "nothing to render". This module
picks the same source and canonicalizes it the same way (TASK-N002's
`canonicalize_math_source`), so the string stored on `MathBlock`/
`MathInline` is exactly what TASK-N003 onward would render and TASK-N004
would cache -- not a second, subtly different copy of the same formula.
"""

from __future__ import annotations

from wikiepwing.normalize.math_node import RawMathNode
from wikiepwing.normalize.math_source import canonicalize_math_source

_TEX_FORMAT = "tex"
_TEXT_ALTERNATIVE_FORMAT = "text_alternative"


def resolve_math_source(node: RawMathNode) -> tuple[str, str] | None:
    """Return `(source, source_format)` for `node`, or None if no source is available."""
    if node.tex_source is not None:
        canonical = canonicalize_math_source(node.tex_source)
        if canonical:
            return canonical, _TEX_FORMAT
    if node.text_alternative is not None:
        canonical = canonicalize_math_source(node.text_alternative)
        if canonical:
            return canonical, _TEXT_ALTERNATIVE_FORMAT
    return None
