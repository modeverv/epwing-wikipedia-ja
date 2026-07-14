"""Duplicate resolution: page ID / revision / hash rules (ARCHITECTURE.md 10.5)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from wikiepwing.ingest.record_parser import RawArticle
from wikiepwing.ingest.validate import Diagnostic


class ResolutionAction(Enum):
    """What happened when comparing a candidate article to the existing one."""

    FIRST_SEEN = "first_seen"
    REPLACED_BY_NEWER_REVISION = "replaced_by_newer_revision"
    KEPT_EXISTING_NEWER_REVISION = "kept_existing_newer_revision"
    IGNORED_IDENTICAL_DUPLICATE = "ignored_identical_duplicate"
    CONFLICT_KEPT_EXISTING = "conflict_kept_existing"


@dataclass(frozen=True, slots=True)
class ExistingArticleState:
    """The already-accepted state for one page_id, as needed to resolve duplicates."""

    revision_id: int
    source_hash: str
    source_sequence: int


@dataclass(frozen=True, slots=True)
class DuplicateRecord:
    """One row to append to the `ingest_duplicates` table."""

    page_id: int
    kept_revision_id: int
    dropped_revision_id: int
    kept_hash: str
    dropped_hash: str
    reason: str
    source_sequence: int


@dataclass(frozen=True, slots=True)
class Resolution:
    """The outcome of comparing a candidate article against any existing state."""

    action: ResolutionAction
    keep_new: bool
    duplicate_record: DuplicateRecord | None
    diagnostic: Diagnostic | None


def resolve_duplicate(existing: ExistingArticleState | None, candidate: RawArticle) -> Resolution:
    """Decide whether `candidate` replaces, is ignored by, or conflicts with `existing`.

    Identity is page_id + revision_id + content hash only; titles are never compared,
    per ARCHITECTURE.md 10.5.
    """
    if existing is None:
        return Resolution(
            action=ResolutionAction.FIRST_SEEN,
            keep_new=True,
            duplicate_record=None,
            diagnostic=None,
        )

    if candidate.revision_id > existing.revision_id:
        return Resolution(
            action=ResolutionAction.REPLACED_BY_NEWER_REVISION,
            keep_new=True,
            duplicate_record=DuplicateRecord(
                page_id=candidate.page_id,
                kept_revision_id=candidate.revision_id,
                dropped_revision_id=existing.revision_id,
                kept_hash=candidate.source_hash,
                dropped_hash=existing.source_hash,
                reason="newer_revision_replaced_older",
                source_sequence=candidate.source_sequence,
            ),
            diagnostic=None,
        )

    if candidate.revision_id < existing.revision_id:
        return Resolution(
            action=ResolutionAction.KEPT_EXISTING_NEWER_REVISION,
            keep_new=False,
            duplicate_record=DuplicateRecord(
                page_id=candidate.page_id,
                kept_revision_id=existing.revision_id,
                dropped_revision_id=candidate.revision_id,
                kept_hash=existing.source_hash,
                dropped_hash=candidate.source_hash,
                reason="out_of_order_older_revision_dropped",
                source_sequence=candidate.source_sequence,
            ),
            diagnostic=None,
        )

    if candidate.source_hash == existing.source_hash:
        return Resolution(
            action=ResolutionAction.IGNORED_IDENTICAL_DUPLICATE,
            keep_new=False,
            duplicate_record=DuplicateRecord(
                page_id=candidate.page_id,
                kept_revision_id=existing.revision_id,
                dropped_revision_id=candidate.revision_id,
                kept_hash=existing.source_hash,
                dropped_hash=candidate.source_hash,
                reason="identical_duplicate_delivery",
                source_sequence=candidate.source_sequence,
            ),
            diagnostic=None,
        )

    return Resolution(
        action=ResolutionAction.CONFLICT_KEPT_EXISTING,
        keep_new=False,
        duplicate_record=DuplicateRecord(
            page_id=candidate.page_id,
            kept_revision_id=existing.revision_id,
            dropped_revision_id=candidate.revision_id,
            kept_hash=existing.source_hash,
            dropped_hash=candidate.source_hash,
            reason="same_revision_conflicting_hash",
            source_sequence=candidate.source_sequence,
        ),
        diagnostic=Diagnostic(
            code="REC_REVISION_HASH_CONFLICT",
            severity="error",
            message=(
                f"article {candidate.page_id} revision {candidate.revision_id} "
                "has conflicting content hashes across deliveries"
            ),
            details={
                "page_id": candidate.page_id,
                "revision_id": candidate.revision_id,
                "existing_hash": existing.source_hash,
                "candidate_hash": candidate.source_hash,
                "existing_source_sequence": existing.source_sequence,
                "candidate_source_sequence": candidate.source_sequence,
            },
        ),
    )
