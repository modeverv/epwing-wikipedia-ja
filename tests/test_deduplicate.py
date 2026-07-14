from __future__ import annotations

import json
from pathlib import Path

from wikiepwing.ingest.deduplicate import (
    ExistingArticleState,
    ResolutionAction,
    resolve_duplicate,
)
from wikiepwing.ingest.record_parser import parse_record

EDGE_CASE_PATH = Path("tests/fixtures/enterprise/edge_case_articles.ndjson")
EDGE_CASE_INDEX_PATH = Path("tests/fixtures/enterprise/edge_case_index.json")


def _lines() -> list[bytes]:
    return [
        line.encode("utf-8")
        for line in EDGE_CASE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _edge_index() -> dict[str, list[int]]:
    return json.loads(EDGE_CASE_INDEX_PATH.read_text(encoding="utf-8"))["scenarios"]


def _existing_from(article, source_sequence: int) -> ExistingArticleState:
    return ExistingArticleState(
        revision_id=article.revision_id,
        source_hash=article.source_hash,
        source_sequence=source_sequence,
    )


def test_first_seen_when_no_existing_state() -> None:
    lines = _lines()
    candidate = parse_record(lines[0], source_sequence=0)

    resolution = resolve_duplicate(None, candidate)

    assert resolution.action == ResolutionAction.FIRST_SEEN
    assert resolution.keep_new is True
    assert resolution.duplicate_record is None
    assert resolution.diagnostic is None


def test_same_page_id_different_revision_scenario_replaces_older() -> None:
    lines = _lines()
    first_index, second_index = _edge_index()["same_page_id_different_revision"]
    older = parse_record(lines[first_index], source_sequence=first_index)
    newer = parse_record(lines[second_index], source_sequence=second_index)
    existing = _existing_from(older, first_index)

    resolution = resolve_duplicate(existing, newer)

    assert resolution.action == ResolutionAction.REPLACED_BY_NEWER_REVISION
    assert resolution.keep_new is True
    assert resolution.duplicate_record is not None
    assert resolution.duplicate_record.kept_revision_id == newer.revision_id
    assert resolution.duplicate_record.dropped_revision_id == older.revision_id
    assert resolution.diagnostic is None


def test_out_of_order_arrival_keeps_existing_newer_revision() -> None:
    lines = _lines()
    first_index, second_index = _edge_index()["same_page_id_different_revision"]
    older = parse_record(lines[first_index], source_sequence=first_index)
    newer = parse_record(lines[second_index], source_sequence=second_index)
    # simulate the newer revision having already been accepted first
    existing = _existing_from(newer, second_index)

    resolution = resolve_duplicate(existing, older)

    assert resolution.action == ResolutionAction.KEPT_EXISTING_NEWER_REVISION
    assert resolution.keep_new is False
    assert resolution.duplicate_record is not None
    assert resolution.duplicate_record.kept_revision_id == newer.revision_id
    assert resolution.duplicate_record.dropped_revision_id == older.revision_id


def test_same_revision_duplicate_hash_scenario_is_ignored() -> None:
    lines = _lines()
    first_index, second_index = _edge_index()["same_revision_duplicate_hash"]
    first = parse_record(lines[first_index], source_sequence=first_index)
    second = parse_record(lines[second_index], source_sequence=second_index)
    existing = _existing_from(first, first_index)

    resolution = resolve_duplicate(existing, second)

    assert resolution.action == ResolutionAction.IGNORED_IDENTICAL_DUPLICATE
    assert resolution.keep_new is False
    assert resolution.duplicate_record is not None
    assert resolution.duplicate_record.reason == "identical_duplicate_delivery"
    assert resolution.diagnostic is None


def test_same_revision_different_hash_scenario_is_a_conflict() -> None:
    lines = _lines()
    first_index, second_index = _edge_index()["same_revision_different_hash"]
    first = parse_record(lines[first_index], source_sequence=first_index)
    second = parse_record(lines[second_index], source_sequence=second_index)
    existing = _existing_from(first, first_index)

    resolution = resolve_duplicate(existing, second)

    assert resolution.action == ResolutionAction.CONFLICT_KEPT_EXISTING
    assert resolution.keep_new is False
    assert resolution.duplicate_record is not None
    assert resolution.duplicate_record.reason == "same_revision_conflicting_hash"
    assert resolution.duplicate_record.kept_hash == first.source_hash
    assert resolution.duplicate_record.dropped_hash == second.source_hash
    assert resolution.diagnostic is not None
    assert resolution.diagnostic.code == "REC_REVISION_HASH_CONFLICT"
    assert resolution.diagnostic.severity == "error"
    assert resolution.diagnostic.details["page_id"] == first.page_id


def test_duplicate_record_source_sequence_is_the_candidates() -> None:
    lines = _lines()
    first_index, second_index = _edge_index()["same_revision_duplicate_hash"]
    first = parse_record(lines[first_index], source_sequence=first_index)
    second = parse_record(lines[second_index], source_sequence=second_index)
    existing = _existing_from(first, first_index)

    resolution = resolve_duplicate(existing, second)

    assert resolution.duplicate_record is not None
    assert resolution.duplicate_record.source_sequence == second_index
