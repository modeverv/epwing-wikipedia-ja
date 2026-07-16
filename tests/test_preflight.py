from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from wikiepwing.config import load_config
from wikiepwing.doctor import CheckResult, DoctorReport
from wikiepwing.preflight import FULL_BUILD_GATE_ITEMS, run_full_build_preflight
from wikiepwing.source.lockfile import (
    SourceLock,
    SourceLockAcquirer,
    SourceLockFile,
    build_source_lock,
)

DEFAULT_CONFIG = Path("config/default.toml")


def _config():  # type: ignore[no-untyped-def]
    return load_config(DEFAULT_CONFIG)


def _empty_doctor_report() -> DoctorReport:
    return DoctorReport(checks=(), generated_at=datetime(2026, 1, 1, tzinfo=UTC))


def _concrete_source_lock() -> SourceLock:
    return build_source_lock(
        provider="wikimedia-enterprise-snapshot",
        project="jawiki",
        namespace=0,
        snapshot_identifier="jawiki_namespace_0",
        snapshot_version="35061ecbd3bc55c31cffd4b46838673d",
        date_modified=datetime(2026, 7, 1, tzinfo=UTC),
        downloaded_at=datetime(2026, 7, 16, tzinfo=UTC),
        files=(
            SourceLockFile(
                relative_path="jawiki_namespace_0_chunk_0.tar.gz",
                chunk_identifier="jawiki_namespace_0_chunk_0",
                size_bytes=1,
                sha256="0" * 64,
                media_type="application/gzip",
            ),
        ),
        metadata_response_sha256="0" * 64,
        acquirer=SourceLockAcquirer(name="wikiepwing", version="0.1.0", git_commit="abc1234"),
    )


def _all_passing_test_suite_results() -> dict[str, bool]:
    return dict.fromkeys(FULL_BUILD_GATE_ITEMS, True)


def test_all_checks_passing_yields_ok_report() -> None:
    report = run_full_build_preflight(
        _config(),
        doctor_report=_empty_doctor_report(),
        source_lock=_concrete_source_lock(),
        test_suite_results=_all_passing_test_suite_results(),
    )

    assert report.ok is True


def test_preserves_existing_doctor_checks() -> None:
    doctor_check = CheckResult(
        name="free_disk",
        category="storage",
        status="pass",
        required=True,
        detail="ok",
        data={},
    )
    doctor_report = DoctorReport(
        checks=(doctor_check,), generated_at=datetime(2026, 1, 1, tzinfo=UTC)
    )

    report = run_full_build_preflight(
        _config(),
        doctor_report=doctor_report,
        source_lock=_concrete_source_lock(),
        test_suite_results=_all_passing_test_suite_results(),
    )

    assert doctor_check in report.checks


def test_non_concrete_source_lock_fails() -> None:
    invalid_lock = SourceLock(
        schema_version=1,
        provider="wikimedia-enterprise-snapshot",
        project="jawiki",
        namespace=0,
        snapshot_identifier="jawiki_namespace_0",
        snapshot_version="latest",
        date_modified=datetime(2026, 7, 1, tzinfo=UTC),
        downloaded_at=datetime(2026, 7, 16, tzinfo=UTC),
        files=(),
        supplements=(),
        metadata_response_sha256="0" * 64,
        acquirer=SourceLockAcquirer(name="wikiepwing", version="0.1.0", git_commit="abc1234"),
    )

    report = run_full_build_preflight(
        _config(),
        doctor_report=_empty_doctor_report(),
        source_lock=invalid_lock,
        test_suite_results=_all_passing_test_suite_results(),
    )

    assert report.ok is False
    failed = {check.name for check in report.checks if check.status == "fail"}
    assert "source_lock_concrete" in failed


def test_missing_test_suite_result_fails_closed() -> None:
    incomplete_results = _all_passing_test_suite_results()
    del incomplete_results["gaiji_test"]

    report = run_full_build_preflight(
        _config(),
        doctor_report=_empty_doctor_report(),
        source_lock=_concrete_source_lock(),
        test_suite_results=incomplete_results,
    )

    assert report.ok is False
    failed = {check.name for check in report.checks if check.status == "fail"}
    assert "gaiji_test" in failed


def test_a_failing_test_suite_result_fails_the_gate() -> None:
    results = _all_passing_test_suite_results()
    results["resume_test"] = False

    report = run_full_build_preflight(
        _config(),
        doctor_report=_empty_doctor_report(),
        source_lock=_concrete_source_lock(),
        test_suite_results=results,
    )

    assert report.ok is False


def test_every_gate_item_appears_as_a_check() -> None:
    report = run_full_build_preflight(
        _config(),
        doctor_report=_empty_doctor_report(),
        source_lock=_concrete_source_lock(),
        test_suite_results=_all_passing_test_suite_results(),
    )

    check_names = {check.name for check in report.checks}
    for item in FULL_BUILD_GATE_ITEMS:
        assert item in check_names


def test_profile_fixed_check_passes_for_default_config() -> None:
    report = run_full_build_preflight(
        _config(),
        doctor_report=_empty_doctor_report(),
        source_lock=_concrete_source_lock(),
        test_suite_results=_all_passing_test_suite_results(),
    )

    profile_check = next(check for check in report.checks if check.name == "profile_fixed")
    assert profile_check.status == "pass"
