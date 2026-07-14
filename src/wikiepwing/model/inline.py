"""Inline model: the initial subset from ARCHITECTURE.md 11.3 (PLAN.md Phase 6 scope)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

Resolution = Literal["resolved", "missing", "externalized"]
_RESOLUTIONS = ("resolved", "missing", "externalized")


class InlineError(ValueError):
    """Raised when an Inline cannot be constructed or decoded safely."""


@dataclass(frozen=True, slots=True)
class TextInline:
    """Plain text content."""

    value: str

    def payload(self) -> dict[str, object]:
        """Return this inline's JSON-serializable representation."""
        return {"type": "text", "value": self.value}


@dataclass(frozen=True, slots=True)
class StrongInline:
    """Strong (bold) emphasis wrapping nested inlines."""

    inlines: tuple[Inline, ...]

    def payload(self) -> dict[str, object]:
        """Return this inline's JSON-serializable representation."""
        return {"type": "strong", "inlines": [inline_payload(inline) for inline in self.inlines]}


@dataclass(frozen=True, slots=True)
class EmphasisInline:
    """Emphasis (italic) wrapping nested inlines."""

    inlines: tuple[Inline, ...]

    def payload(self) -> dict[str, object]:
        """Return this inline's JSON-serializable representation."""
        return {"type": "emphasis", "inlines": [inline_payload(inline) for inline in self.inlines]}


@dataclass(frozen=True, slots=True)
class CodeInline:
    """Inline code/monospace text."""

    value: str

    def payload(self) -> dict[str, object]:
        """Return this inline's JSON-serializable representation."""
        return {"type": "code", "value": self.value}


@dataclass(frozen=True, slots=True)
class LineBreakInline:
    """An explicit line break within a block."""

    def payload(self) -> dict[str, object]:
        """Return this inline's JSON-serializable representation."""
        return {"type": "line_break"}


@dataclass(frozen=True, slots=True)
class InternalLinkInline:
    """A link resolved (or not) to another article by title/page ID (ARCHITECTURE.md 11.4)."""

    label: tuple[Inline, ...]
    target_title: str
    target_normalized_title: str
    target_fragment: str | None
    target_page_id: int | None
    resolution: Resolution

    def __post_init__(self) -> None:
        if not self.target_title:
            raise InlineError("target_title must be a non-empty string")
        if not self.target_normalized_title:
            raise InlineError("target_normalized_title must be a non-empty string")
        if self.resolution not in _RESOLUTIONS:
            raise InlineError(f"resolution must be one of {_RESOLUTIONS}: {self.resolution!r}")

    def payload(self) -> dict[str, object]:
        """Return this inline's JSON-serializable representation."""
        return {
            "type": "internal_link",
            "label": [inline_payload(inline) for inline in self.label],
            "target_title": self.target_title,
            "target_normalized_title": self.target_normalized_title,
            "target_fragment": self.target_fragment,
            "target_page_id": self.target_page_id,
            "resolution": self.resolution,
        }


@dataclass(frozen=True, slots=True)
class ExternalLinkInline:
    """A link to a resource outside the dictionary's own articles."""

    label: tuple[Inline, ...]
    url: str

    def __post_init__(self) -> None:
        if not self.url:
            raise InlineError("url must be a non-empty string")

    def payload(self) -> dict[str, object]:
        """Return this inline's JSON-serializable representation."""
        return {
            "type": "external_link",
            "label": [inline_payload(inline) for inline in self.label],
            "url": self.url,
        }


@dataclass(frozen=True, slots=True)
class UnsupportedInline:
    """A fallback for any inline content not yet modeled explicitly."""

    element_name: str
    fallback_text: str
    diagnostic_code: str

    def __post_init__(self) -> None:
        if not self.element_name:
            raise InlineError("element_name must be a non-empty string")
        if not self.diagnostic_code:
            raise InlineError("diagnostic_code must be a non-empty string")

    def payload(self) -> dict[str, object]:
        """Return this inline's JSON-serializable representation."""
        return {
            "type": "unsupported",
            "element_name": self.element_name,
            "fallback_text": self.fallback_text,
            "diagnostic_code": self.diagnostic_code,
        }


Inline = (
    TextInline
    | StrongInline
    | EmphasisInline
    | CodeInline
    | LineBreakInline
    | InternalLinkInline
    | ExternalLinkInline
    | UnsupportedInline
)


def inline_payload(inline: Inline) -> dict[str, object]:
    """Return any Inline's JSON-serializable representation."""
    return inline.payload()


def parse_inline(payload: object) -> Inline:
    """Parse one JSON object into an Inline. Unknown `type` values are a codec error."""
    if not isinstance(payload, dict):
        raise InlineError("inline must be a JSON object")
    fields = cast(dict[str, object], payload)
    kind = fields.get("type")
    if kind == "text":
        return TextInline(value=_require_str(fields, "value"))
    if kind == "strong":
        return StrongInline(inlines=_parse_inline_list(fields, "inlines"))
    if kind == "emphasis":
        return EmphasisInline(inlines=_parse_inline_list(fields, "inlines"))
    if kind == "code":
        return CodeInline(value=_require_str(fields, "value"))
    if kind == "line_break":
        return LineBreakInline()
    if kind == "internal_link":
        return InternalLinkInline(
            label=_parse_inline_list(fields, "label"),
            target_title=_require_str(fields, "target_title"),
            target_normalized_title=_require_str(fields, "target_normalized_title"),
            target_fragment=_optional_str(fields, "target_fragment"),
            target_page_id=_optional_int(fields, "target_page_id"),
            resolution=cast(Resolution, _require_str(fields, "resolution")),
        )
    if kind == "external_link":
        return ExternalLinkInline(
            label=_parse_inline_list(fields, "label"),
            url=_require_str(fields, "url"),
        )
    if kind == "unsupported":
        return UnsupportedInline(
            element_name=_require_str(fields, "element_name"),
            fallback_text=_optional_str(fields, "fallback_text") or "",
            diagnostic_code=_require_str(fields, "diagnostic_code"),
        )
    raise InlineError(f"unknown inline type: {kind!r}")


def _require_str(fields: dict[str, object], key: str) -> str:
    value = fields.get(key)
    if not isinstance(value, str):
        raise InlineError(f"inline is missing a string field: {key}")
    return value


def _optional_str(fields: dict[str, object], key: str) -> str | None:
    value = fields.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise InlineError(f"inline field {key} must be a string or null")
    return value


def _optional_int(fields: dict[str, object], key: str) -> int | None:
    value = fields.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise InlineError(f"inline field {key} must be an integer or null")
    return value


def _parse_inline_list(fields: dict[str, object], key: str) -> tuple[Inline, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise InlineError(f"inline is missing an array field: {key}")
    return tuple(parse_inline(item) for item in cast(list[object], value))
