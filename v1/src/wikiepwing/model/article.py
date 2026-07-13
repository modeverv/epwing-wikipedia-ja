"""Versioned immutable intermediate article representation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

SCHEMA_VERSION = 2


@dataclass(frozen=True, slots=True)
class Inline:
    text: str
    target: str | None = None


@dataclass(frozen=True, slots=True)
class MediaReference:
    file_name: str
    caption: str = ""
    source: str = "article"

    def __post_init__(self) -> None:
        if not self.file_name:
            raise ValueError("media file name must not be empty")
        if self.source not in {"article", "infobox"}:
            raise ValueError(f"unknown media source: {self.source}")


@dataclass(frozen=True, slots=True)
class Block:
    kind: str
    inlines: tuple[Inline, ...]
    level: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"paragraph", "heading", "list_item", "preformatted", "rule"}:
            raise ValueError(f"unknown block kind: {self.kind}")
        if self.kind == "heading" and (self.level is None or not 1 <= self.level <= 6):
            raise ValueError("heading level must be between 1 and 6")
        if self.kind != "heading" and self.level is not None:
            raise ValueError("only heading blocks may have a level")


@dataclass(frozen=True, slots=True)
class Article:
    page_id: int
    title: str
    blocks: tuple[Block, ...]
    aliases: tuple[str, ...] = ()
    media: tuple[MediaReference, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported article schema version")
        if not self.title:
            raise ValueError("article title must not be empty")

    def to_json(self) -> str:
        """Return a deterministic debugging serialization."""
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
