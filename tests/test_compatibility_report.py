from __future__ import annotations

import json
from pathlib import Path

from wikiepwing.compatibility.comparison import (
    DEFAULT_THRESHOLDS,
    QueryHitSet,
    compare_query_results,
    evaluate_thresholds,
)
from wikiepwing.compatibility.report import build_compatibility_report, write_compatibility_report


def _evaluation():  # type: ignore[no-untyped-def]
    reference = [QueryHitSet(query_key="q1", expected_presence=True, headings=("Emacs",))]
    candidate = [QueryHitSet(query_key="q1", expected_presence=True, headings=("Emacs",))]
    summary = compare_query_results(reference, candidate)
    return evaluate_thresholds(summary, DEFAULT_THRESHOLDS)


def test_build_compatibility_report_matches_schema_fields() -> None:
    evaluation = _evaluation()

    payload = build_compatibility_report(
        reference_name="local-reference-2023",
        reference_fingerprint="sha256:abc",
        candidate_profile="full",
        candidate_artifact_hash="sha256:def",
        evaluation=evaluation,
    )

    assert payload["schema_version"] == 1
    assert payload["reference"] == {"name": "local-reference-2023", "fingerprint": "sha256:abc"}
    assert payload["candidate"] == {"profile": "full", "artifact_hash": "sha256:def"}
    assert payload["queries"] == {
        "total": 1,
        "target_coverage": 1.0,
        "false_positive_count": 0,
        "overlap_at_n_mean": 1.0,
    }
    assert payload["thresholds"] == {"min_target_coverage": 0.95, "max_false_positives": 0}
    assert payload["status"] == "pass"


def test_build_compatibility_report_is_json_serializable() -> None:
    payload = build_compatibility_report(
        reference_name="ref",
        reference_fingerprint="sha256:x",
        candidate_profile="mini",
        candidate_artifact_hash="sha256:y",
        evaluation=_evaluation(),
    )

    json.dumps(payload)


def test_write_compatibility_report_writes_json_and_html(tmp_path: Path) -> None:
    payload = build_compatibility_report(
        reference_name="ref",
        reference_fingerprint="sha256:x",
        candidate_profile="mini",
        candidate_artifact_hash="sha256:y",
        evaluation=_evaluation(),
    )

    json_path, html_path = write_compatibility_report(payload, tmp_path)

    assert json_path.is_file()
    assert html_path.is_file()
    assert json.loads(json_path.read_text(encoding="utf-8")) == payload
    html_text = html_path.read_text(encoding="utf-8")
    assert "pass" in html_text
    assert "target_coverage" in html_text


def test_write_compatibility_report_html_reflects_fail_status(tmp_path: Path) -> None:
    reference = [QueryHitSet(query_key="q1", expected_presence=True, headings=("Emacs",))]
    candidate = [QueryHitSet(query_key="q1", expected_presence=True, headings=())]
    summary = compare_query_results(reference, candidate)
    evaluation = evaluate_thresholds(summary, DEFAULT_THRESHOLDS)
    payload = build_compatibility_report(
        reference_name="ref",
        reference_fingerprint="sha256:x",
        candidate_profile="mini",
        candidate_artifact_hash="sha256:y",
        evaluation=evaluation,
    )

    _json_path, html_path = write_compatibility_report(payload, tmp_path)

    html_text = html_path.read_text(encoding="utf-8")
    assert "status-fail" in html_text


def test_write_compatibility_report_creates_missing_directory(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "reports"
    payload = build_compatibility_report(
        reference_name="ref",
        reference_fingerprint="sha256:x",
        candidate_profile="mini",
        candidate_artifact_hash="sha256:y",
        evaluation=_evaluation(),
    )

    json_path, html_path = write_compatibility_report(payload, destination)

    assert json_path.is_file()
    assert html_path.is_file()


def test_build_compatibility_report_handles_none_overlap() -> None:
    reference = [QueryHitSet(query_key="missing", expected_presence=False, headings=())]
    candidate = [QueryHitSet(query_key="missing", expected_presence=False, headings=())]
    summary = compare_query_results(reference, candidate)
    evaluation = evaluate_thresholds(summary, DEFAULT_THRESHOLDS)

    payload = build_compatibility_report(
        reference_name="ref",
        reference_fingerprint="sha256:x",
        candidate_profile="mini",
        candidate_artifact_hash="sha256:y",
        evaluation=evaluation,
    )

    assert payload["queries"]["overlap_at_n_mean"] is None  # type: ignore[index]


def test_write_compatibility_report_renders_html_with_none_overlap(tmp_path: Path) -> None:
    reference = [QueryHitSet(query_key="missing", expected_presence=False, headings=())]
    candidate = [QueryHitSet(query_key="missing", expected_presence=False, headings=())]
    summary = compare_query_results(reference, candidate)
    evaluation = evaluate_thresholds(summary, DEFAULT_THRESHOLDS)
    payload = build_compatibility_report(
        reference_name="ref",
        reference_fingerprint="sha256:x",
        candidate_profile="mini",
        candidate_artifact_hash="sha256:y",
        evaluation=evaluation,
    )

    _json_path, html_path = write_compatibility_report(payload, tmp_path)

    assert "n/a" in html_path.read_text(encoding="utf-8")
