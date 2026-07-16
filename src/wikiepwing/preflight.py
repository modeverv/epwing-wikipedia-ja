"""Full-build preflight gate (TASK-R002, PLAN.md 30 "Full build前ゲート一覧").

`run_full_build_preflight` combines `doctor.run_doctor`'s existing
environment checks (disk capacity, path writability/persistence,
configuration validity -- already covering 30's "Docker disk capacity
verified" and "logs/reports persistent" items) with the full-build-specific
items 30 lists:

- `source lock concrete`: `source.lock.json` must record a resolved,
  concrete `snapshot_version`, never the literal string `"latest"` --
  `acquire_snapshot` always resolves "latest" to a real version
  identifier, so this mostly guards against a hand-edited lock file.
- `user-facing profile settings fixed`: `config.profile` must be one of
  the three known profiles (already enforced when the config loads;
  this is a defensive re-check at the gate itself).
- Every other item in 30's checklist ("Phase 0〜20完了", "toolchain
  smoke green", "reference scan complete", "100記事Mini/Lite green",
  "10,000記事Lite green", "resume test green", "gaiji test green",
  "image security test green", "no network after acquire verified") is
  "did a specific test/smoke suite run and pass" -- something only the
  caller (having actually run `make check`, the Docker smoke scripts,
  etc.) can know, not something this process can introspect on its own.
  Those come in as `test_suite_results`, and a missing required item
  fails closed rather than being silently skipped.
"""

from __future__ import annotations

from collections.abc import Mapping

from wikiepwing.config import AppConfig
from wikiepwing.doctor import CheckResult, DoctorReport
from wikiepwing.source.lockfile import SourceLock

#: PLAN.md 30's "has a specific test/smoke suite been run and passed"
#: items -- every key here must appear in `test_suite_results`.
FULL_BUILD_GATE_ITEMS = (
    "toolchain_smoke",
    "reference_scan",
    "hundred_article_mini",
    "hundred_article_lite",
    "ten_thousand_article_lite",
    "resume_test",
    "gaiji_test",
    "image_security_test",
    "no_network_after_acquire",
)


def run_full_build_preflight(
    config: AppConfig,
    *,
    doctor_report: DoctorReport,
    source_lock: SourceLock,
    test_suite_results: Mapping[str, bool],
) -> DoctorReport:
    """Combine `doctor_report` with PLAN.md 30's remaining full-build gate items."""
    checks = list(doctor_report.checks)
    checks.append(_source_lock_concrete_check(source_lock))
    checks.append(_profile_fixed_check(config))
    for item in FULL_BUILD_GATE_ITEMS:
        checks.append(_test_suite_check(item, test_suite_results))
    return DoctorReport(
        checks=tuple(checks),
        generated_at=doctor_report.generated_at,
        configuration_error=doctor_report.configuration_error,
    )


def _source_lock_concrete_check(source_lock: SourceLock) -> CheckResult:
    is_concrete = source_lock.snapshot_version != "latest"
    return CheckResult(
        name="source_lock_concrete",
        category="release-gate",
        status="pass" if is_concrete else "fail",
        required=True,
        detail=(
            f"source.lock.json resolved to {source_lock.snapshot_version!r}"
            if is_concrete
            else "source.lock.json must record a resolved version, not the literal 'latest'"
        ),
        data={"snapshot_version": source_lock.snapshot_version},
    )


def _profile_fixed_check(config: AppConfig) -> CheckResult:
    known_profiles = ("mini", "lite", "full")
    is_fixed = config.profile in known_profiles
    return CheckResult(
        name="profile_fixed",
        category="release-gate",
        status="pass" if is_fixed else "fail",
        required=True,
        detail=f"profile is {config.profile!r}"
        if is_fixed
        else f"profile must be one of {known_profiles}: {config.profile!r}",
        data={"profile": config.profile},
    )


def _test_suite_check(name: str, test_suite_results: Mapping[str, bool]) -> CheckResult:
    if name not in test_suite_results:
        return CheckResult(
            name=name,
            category="release-gate",
            status="fail",
            required=True,
            detail=f"test_suite_results is missing required item: {name!r}",
            data={},
        )
    passed = test_suite_results[name]
    return CheckResult(
        name=name,
        category="release-gate",
        status="pass" if passed else "fail",
        required=True,
        detail=f"{name} {'passed' if passed else 'failed'}",
        data={},
    )
