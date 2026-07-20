"""Safe, declarative-scale template fallback behavior."""

from __future__ import annotations

from dataclasses import dataclass

DROP_TEMPLATES = frozenset({"cleanup", "citation needed", "stub"})


@dataclass(frozen=True, slots=True)
class TemplateResult:
    text: str
    diagnostic: str | None


def render_template(
    name: str, positional: tuple[str, ...], named: tuple[tuple[str, str], ...] = ()
) -> TemplateResult:
    """Apply minimal safe rules and preserve unknown arguments as readable text."""
    normalized = " ".join(name.replace("_", " ").split()).casefold()
    if normalized in DROP_TEMPLATES:
        return TemplateResult("", None)
    parts = list(positional) + [f"{key}: {value}" for key, value in named]
    body = "; ".join(part for part in parts if part.strip())
    return TemplateResult(body or name, "TEMPLATE_UNSUPPORTED")
