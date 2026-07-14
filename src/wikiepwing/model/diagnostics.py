"""Model-layer Diagnostic: a stable, self-contained per-finding record (ARCHITECTURE.md 11.7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

Severity = Literal["info", "warning", "error", "fatal"]
_SEVERITIES = ("info", "warning", "error", "fatal")


class DiagnosticError(ValueError):
    """Raised when a Diagnostic cannot be constructed or decoded safely."""


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One structured finding attached directly to an Article.

    Unlike `wikiepwing.ingest.validate.Diagnostic` (which relies on the caller to
    supply stage/page_id/title context when persisting it), this model-layer
    Diagnostic is self-contained: it carries everything needed to serialize inside
    an Article's `diagnostics` array without external context. `code` is a stable
    API per ARCHITECTURE.md 11.7.
    """

    code: str
    severity: Severity
    stage: str
    page_id: int | None
    title: str | None
    message: str
    source_path: str | None
    source_excerpt: str | None
    details: dict[str, object]

    def __post_init__(self) -> None:
        if not self.code:
            raise DiagnosticError("code must be a non-empty string")
        if self.severity not in _SEVERITIES:
            raise DiagnosticError(f"severity must be one of {_SEVERITIES}: {self.severity!r}")
        if not self.stage:
            raise DiagnosticError("stage must be a non-empty string")
        if not self.message:
            raise DiagnosticError("message must be a non-empty string")

    def payload(self) -> dict[str, object]:
        """Return this diagnostic's JSON-serializable representation."""
        return {
            "code": self.code,
            "severity": self.severity,
            "stage": self.stage,
            "page_id": self.page_id,
            "title": self.title,
            "message": self.message,
            "source_path": self.source_path,
            "source_excerpt": self.source_excerpt,
            "details": self.details,
        }


def parse_diagnostic(payload: object) -> Diagnostic:
    """Parse one JSON object into a Diagnostic (the inverse of `Diagnostic.payload`)."""
    if not isinstance(payload, dict):
        raise DiagnosticError("diagnostic must be a JSON object")
    fields = cast(dict[str, object], payload)
    return Diagnostic(
        code=_require_str(fields, "code"),
        severity=cast(Severity, _require_str(fields, "severity")),
        stage=_require_str(fields, "stage"),
        page_id=_optional_int(fields, "page_id"),
        title=_optional_str(fields, "title"),
        message=_require_str(fields, "message"),
        source_path=_optional_str(fields, "source_path"),
        source_excerpt=_optional_str(fields, "source_excerpt"),
        details=_require_dict(fields, "details"),
    )


def _require_str(fields: dict[str, object], key: str) -> str:
    value = fields.get(key)
    if not isinstance(value, str) or not value:
        raise DiagnosticError(f"diagnostic is missing a non-empty string field: {key}")
    return value


def _optional_str(fields: dict[str, object], key: str) -> str | None:
    value = fields.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise DiagnosticError(f"diagnostic field {key} must be a string or null")
    return value


def _optional_int(fields: dict[str, object], key: str) -> int | None:
    value = fields.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise DiagnosticError(f"diagnostic field {key} must be an integer or null")
    return value


def _require_dict(fields: dict[str, object], key: str) -> dict[str, object]:
    value = fields.get(key)
    if not isinstance(value, dict):
        raise DiagnosticError(f"diagnostic is missing an object field: {key}")
    return cast(dict[str, object], value)
