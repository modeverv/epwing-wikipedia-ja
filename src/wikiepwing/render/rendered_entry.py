"""RenderedEntry (TASK-H006, ARCHITECTURE.md 16).

The output of converting one Article into a Mini-profile EPWING entry.
Construction here is limited to the type/validation; converting an Article
into a RenderedEntry is TASK-H007 (Mini layout renderer).
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.render.render_node import RenderNode


class RenderedEntryError(ValueError):
    """Raised when a RenderedEntry cannot be constructed safely."""


@dataclass(frozen=True, slots=True)
class RenderedEntry:
    """One rendered EPWING entry (ARCHITECTURE.md 16)."""

    entry_id: str
    page_id: int
    title: str
    headwords: tuple[str, ...]
    body: tuple[RenderNode, ...]
    internal_targets: tuple[str, ...]
    graphics: tuple[str, ...]
    estimated_size: int
    diagnostics: tuple[Diagnostic, ...]
    keywords: tuple[str, ...] = ()
    heading: str | None = None

    def __post_init__(self) -> None:
        if not self.entry_id:
            raise RenderedEntryError("entry_id must be a non-empty string")
        if self.page_id < 1:
            raise RenderedEntryError(f"page_id must be positive: {self.page_id!r}")
        if not self.title:
            raise RenderedEntryError("title must be a non-empty string")
        if self.heading is not None and not self.heading:
            raise RenderedEntryError("heading must be non-empty when present")
        if self.estimated_size < 0:
            raise RenderedEntryError(f"estimated_size must be >= 0: {self.estimated_size!r}")
