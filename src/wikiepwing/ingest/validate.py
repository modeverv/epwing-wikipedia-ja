"""Record safety validation: field length/format limits before repository storage."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import cast

from wikiepwing.config import AppConfig
from wikiepwing.ingest.record_parser import RawArticle


class ValidationConfigError(ValueError):
    """Raised when validation limits themselves are invalid."""


@dataclass(frozen=True, slots=True)
class ValidationLimits:
    """Configured field-size and namespace limits used to validate one article."""

    max_title_bytes: int
    max_url_bytes: int
    max_html_bytes: int
    max_wikitext_bytes: int
    expected_namespace_id: int

    def __post_init__(self) -> None:
        for name in ("max_title_bytes", "max_url_bytes", "max_html_bytes", "max_wikitext_bytes"):
            if getattr(self, name) < 1:
                raise ValidationConfigError(f"{name} must be positive")

    @classmethod
    def from_config(cls, config: AppConfig, *, expected_namespace_id: int) -> ValidationLimits:
        """Build limits from the `[ingest]` configuration section."""
        ingest = config.section("ingest")
        return cls(
            max_title_bytes=cast(int, ingest["max_title_bytes"]),
            max_url_bytes=cast(int, ingest["max_url_bytes"]),
            max_html_bytes=cast(int, ingest["max_html_bytes"]),
            max_wikitext_bytes=cast(int, ingest["max_wikitext_bytes"]),
            expected_namespace_id=expected_namespace_id,
        )


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One structured, per-article validation finding."""

    code: str
    severity: str
    message: str
    details: dict[str, object]

    def __post_init__(self) -> None:
        if self.severity not in ("info", "warning", "error", "fatal"):
            raise ValidationConfigError(f"invalid diagnostic severity: {self.severity}")


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Whether one article is safe to store, plus the diagnostics that led there."""

    accepted: bool
    diagnostics: tuple[Diagnostic, ...]


def validate_article(article: RawArticle, limits: ValidationLimits) -> ValidationResult:
    """Validate one parsed article's field lengths, URL, namespace, and body sizes."""
    diagnostics: list[Diagnostic] = []

    _check_length(
        diagnostics,
        article.title,
        limits.max_title_bytes,
        code="REC_TITLE_TOO_LONG",
        field="title",
        page_id=article.page_id,
    )
    _check_length(
        diagnostics,
        article.url,
        limits.max_url_bytes,
        code="REC_URL_TOO_LONG",
        field="url",
        page_id=article.page_id,
    )
    if not _is_valid_https_url(article.url):
        diagnostics.append(
            Diagnostic(
                code="REC_INVALID_URL",
                severity="error",
                message=f"article {article.page_id} has an invalid or non-https url",
                details={"page_id": article.page_id, "url": article.url},
            )
        )
    if article.namespace_id != limits.expected_namespace_id:
        diagnostics.append(
            Diagnostic(
                code="REC_UNEXPECTED_NAMESPACE",
                severity="error",
                message=(
                    f"article {article.page_id} has namespace {article.namespace_id}, "
                    f"expected {limits.expected_namespace_id}"
                ),
                details={
                    "page_id": article.page_id,
                    "namespace_id": article.namespace_id,
                    "expected_namespace_id": limits.expected_namespace_id,
                },
            )
        )
    if article.html is not None:
        _check_length(
            diagnostics,
            article.html,
            limits.max_html_bytes,
            code="REC_HTML_TOO_LARGE",
            field="html",
            page_id=article.page_id,
        )
    if article.wikitext is not None:
        _check_length(
            diagnostics,
            article.wikitext,
            limits.max_wikitext_bytes,
            code="REC_WIKITEXT_TOO_LARGE",
            field="wikitext",
            page_id=article.page_id,
        )

    accepted = not any(diagnostic.severity in ("error", "fatal") for diagnostic in diagnostics)
    return ValidationResult(accepted=accepted, diagnostics=tuple(diagnostics))


def _check_length(
    diagnostics: list[Diagnostic],
    value: str,
    max_bytes: int,
    *,
    code: str,
    field: str,
    page_id: int,
) -> None:
    size = len(value.encode("utf-8"))
    if size > max_bytes:
        diagnostics.append(
            Diagnostic(
                code=code,
                severity="error",
                message=f"article {page_id} field {field} exceeded {max_bytes} bytes: {size}",
                details={
                    "page_id": page_id,
                    "field": field,
                    "size_bytes": size,
                    "max_bytes": max_bytes,
                },
            )
        )


def _is_valid_https_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)
