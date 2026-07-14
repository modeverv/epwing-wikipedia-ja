"""Article model: the top-level normalized record (ARCHITECTURE.md 11.1).

Also implements the two record types it embeds: `Alias` (ARCHITECTURE.md 13.3,
"aliasにはsourceとconfidenceを付けます") and `MediaReference` (ARCHITECTURE.md
15.2, in full). This module defines shapes and a JSON codec only; validation
rules (TASK-F005) and the canonical/hash codec (TASK-F006) are separate tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, cast

from wikiepwing.model.blocks import Block, block_payload, parse_block
from wikiepwing.model.diagnostics import Diagnostic, parse_diagnostic

AliasSource = Literal[
    "redirect",
    "title",
    "normalized_title_variant",
    "html_display_title",
    "lead_bold",
    "wikidata",
]
_ALIAS_SOURCES = (
    "redirect",
    "title",
    "normalized_title_variant",
    "html_display_title",
    "lead_bold",
    "wikidata",
)

MediaRole = Literal["main", "infobox", "lead", "body", "icon", "unknown"]
_MEDIA_ROLES = ("main", "infobox", "lead", "body", "icon", "unknown")


class ArticleError(ValueError):
    """Raised when an Article (or an Alias/MediaReference it embeds) is invalid."""


@dataclass(frozen=True, slots=True)
class Alias:
    """One alternate name candidate for an article (ARCHITECTURE.md 13.3)."""

    title: str
    source: AliasSource
    confidence: float

    def __post_init__(self) -> None:
        if not self.title:
            raise ArticleError("alias title must be a non-empty string")
        if self.source not in _ALIAS_SOURCES:
            raise ArticleError(f"alias source must be one of {_ALIAS_SOURCES}: {self.source!r}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ArticleError(f"alias confidence must be between 0.0 and 1.0: {self.confidence!r}")

    def payload(self) -> dict[str, object]:
        """Return this alias's JSON-serializable representation."""
        return {"title": self.title, "source": self.source, "confidence": self.confidence}


@dataclass(frozen=True, slots=True)
class MediaReference:
    """A reference to an image/media file used by an article (ARCHITECTURE.md 15.2).

    Normalization stores only the reference; the media itself is downloaded in a
    separate stage (ARCHITECTURE.md 15.1).
    """

    media_id: str
    source_url: str
    source_name: str | None
    alt_text: str | None
    caption: str | None
    role: MediaRole
    source_width: int | None
    source_height: int | None

    def __post_init__(self) -> None:
        if not self.media_id:
            raise ArticleError("media_id must be a non-empty string")
        if not self.source_url:
            raise ArticleError("source_url must be a non-empty string")
        if self.role not in _MEDIA_ROLES:
            raise ArticleError(f"role must be one of {_MEDIA_ROLES}: {self.role!r}")
        if self.source_width is not None and self.source_width < 0:
            raise ArticleError(f"source_width must be >= 0: {self.source_width!r}")
        if self.source_height is not None and self.source_height < 0:
            raise ArticleError(f"source_height must be >= 0: {self.source_height!r}")

    def payload(self) -> dict[str, object]:
        """Return this media reference's JSON-serializable representation."""
        return {
            "media_id": self.media_id,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "alt_text": self.alt_text,
            "caption": self.caption,
            "role": self.role,
            "source_width": self.source_width,
            "source_height": self.source_height,
        }


@dataclass(frozen=True, slots=True)
class Article:
    """The top-level normalized record for one Wikipedia article (ARCHITECTURE.md 11.1)."""

    page_id: int
    revision_id: int
    title: str
    normalized_title: str
    source_url: str
    source_date_modified: datetime
    abstract: str | None
    blocks: tuple[Block, ...]
    aliases: tuple[Alias, ...]
    categories: tuple[str, ...]
    media: tuple[MediaReference, ...]
    diagnostics: tuple[Diagnostic, ...]
    source_license_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.title:
            raise ArticleError("title must be a non-empty string")
        if not self.normalized_title:
            raise ArticleError("normalized_title must be a non-empty string")
        if not self.source_url:
            raise ArticleError("source_url must be a non-empty string")
        if self.source_date_modified.tzinfo is None:
            raise ArticleError("source_date_modified must be timezone-aware")

    def payload(self) -> dict[str, object]:
        """Return this article's JSON-serializable representation."""
        return {
            "page_id": self.page_id,
            "revision_id": self.revision_id,
            "title": self.title,
            "normalized_title": self.normalized_title,
            "source_url": self.source_url,
            "source_date_modified": _format_datetime(self.source_date_modified),
            "abstract": self.abstract,
            "blocks": [block_payload(block) for block in self.blocks],
            "aliases": [alias.payload() for alias in self.aliases],
            "categories": list(self.categories),
            "media": [media.payload() for media in self.media],
            "diagnostics": [diagnostic.payload() for diagnostic in self.diagnostics],
            "source_license_ids": list(self.source_license_ids),
        }


def parse_article(payload: object) -> Article:
    """Parse one JSON object into an Article (the inverse of `Article.payload`)."""
    if not isinstance(payload, dict):
        raise ArticleError("article must be a JSON object")
    fields = cast(dict[str, object], payload)
    return Article(
        page_id=_require_int(fields, "page_id"),
        revision_id=_require_int(fields, "revision_id"),
        title=_require_str(fields, "title"),
        normalized_title=_require_str(fields, "normalized_title"),
        source_url=_require_str(fields, "source_url"),
        source_date_modified=_parse_datetime(_require_str(fields, "source_date_modified")),
        abstract=_optional_str(fields, "abstract"),
        blocks=_parse_block_list(fields, "blocks"),
        aliases=_parse_alias_list(fields, "aliases"),
        categories=_parse_str_list(fields, "categories"),
        media=_parse_media_list(fields, "media"),
        diagnostics=_parse_diagnostic_list(fields, "diagnostics"),
        source_license_ids=_parse_str_list(fields, "source_license_ids"),
    )


def parse_alias(payload: object) -> Alias:
    """Parse one JSON object into an Alias."""
    if not isinstance(payload, dict):
        raise ArticleError("alias must be a JSON object")
    fields = cast(dict[str, object], payload)
    return Alias(
        title=_require_str(fields, "title"),
        source=cast(AliasSource, _require_str(fields, "source")),
        confidence=_require_float(fields, "confidence"),
    )


def parse_media_reference(payload: object) -> MediaReference:
    """Parse one JSON object into a MediaReference."""
    if not isinstance(payload, dict):
        raise ArticleError("media reference must be a JSON object")
    fields = cast(dict[str, object], payload)
    return MediaReference(
        media_id=_require_str(fields, "media_id"),
        source_url=_require_str(fields, "source_url"),
        source_name=_optional_str(fields, "source_name"),
        alt_text=_optional_str(fields, "alt_text"),
        caption=_optional_str(fields, "caption"),
        role=cast(MediaRole, _require_str(fields, "role")),
        source_width=_optional_int(fields, "source_width"),
        source_height=_optional_int(fields, "source_height"),
    )


def _format_datetime(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ArticleError(
            f"source_date_modified is not a valid ISO-8601 datetime: {value!r}"
        ) from error
    if parsed.tzinfo is None:
        raise ArticleError("source_date_modified must be timezone-aware")
    return parsed


def _require_str(fields: dict[str, object], key: str) -> str:
    value = fields.get(key)
    if not isinstance(value, str):
        raise ArticleError(f"article is missing a string field: {key}")
    return value


def _optional_str(fields: dict[str, object], key: str) -> str | None:
    value = fields.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ArticleError(f"article field {key} must be a string or null")
    return value


def _require_int(fields: dict[str, object], key: str) -> int:
    value = fields.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ArticleError(f"article is missing an integer field: {key}")
    return value


def _optional_int(fields: dict[str, object], key: str) -> int | None:
    value = fields.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ArticleError(f"article field {key} must be an integer or null")
    return value


def _require_float(fields: dict[str, object], key: str) -> float:
    value = fields.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ArticleError(f"article is missing a numeric field: {key}")
    return float(value)


def _parse_str_list(fields: dict[str, object], key: str) -> tuple[str, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise ArticleError(f"article is missing an array field: {key}")
    items = cast(list[object], value)
    for item in items:
        if not isinstance(item, str):
            raise ArticleError(f"article field {key} must be an array of strings")
    return tuple(cast(list[str], items))


def _parse_block_list(fields: dict[str, object], key: str) -> tuple[Block, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise ArticleError(f"article is missing an array field: {key}")
    return tuple(parse_block(item) for item in cast(list[object], value))


def _parse_alias_list(fields: dict[str, object], key: str) -> tuple[Alias, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise ArticleError(f"article is missing an array field: {key}")
    return tuple(parse_alias(item) for item in cast(list[object], value))


def _parse_media_list(fields: dict[str, object], key: str) -> tuple[MediaReference, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise ArticleError(f"article is missing an array field: {key}")
    return tuple(parse_media_reference(item) for item in cast(list[object], value))


def _parse_diagnostic_list(fields: dict[str, object], key: str) -> tuple[Diagnostic, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise ArticleError(f"article is missing an array field: {key}")
    return tuple(parse_diagnostic(item) for item in cast(list[object], value))
