"""Stable EPWING entry IDs (TASK-H005, ARCHITECTURE.md 16.1).

Entry IDs are derived from `page_id` alone (`p<page_id>`, e.g. `p12345`) so
that internal cross-references survive title changes.
"""

from __future__ import annotations


class EntryIdError(ValueError):
    """Raised when a stable entry ID cannot be computed."""


def compute_entry_id(page_id: int) -> str:
    """Return the stable EPWING entry ID for `page_id` (ARCHITECTURE.md 16.1: `p<page_id>`)."""
    if page_id < 1:
        raise EntryIdError(f"page_id must be positive: {page_id!r}")
    return f"p{page_id}"
