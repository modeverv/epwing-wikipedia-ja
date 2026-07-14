"""Resume decision (TASK-I005, ARCHITECTURE.md 7.2 "manifest比較"/"resume判定").

A stage's previous manifest can be *reused* (the stage skipped entirely)
only when all of the following hold: a previous manifest exists, it
finished with status "complete", its `stage_version` matches the stage's
current version, and its recorded `inputs` fingerprints match the inputs
computed for the current run. Any mismatch means the previous outputs are
stale (or absent) and the stage must run again.

This module only decides; wiring it into the ingest/normalize/generate
orchestrators (and the `--from-stage`/`--force-stage` CLI flags) is
TASK-I006's job.
"""

from __future__ import annotations

from dataclasses import dataclass

_COMPLETE_STATUS = "complete"


@dataclass(frozen=True, slots=True)
class ResumeDecision:
    """Whether a stage can be skipped, and why."""

    should_skip: bool
    reason: str


def decide_resume(
    previous_manifest: dict[str, object] | None,
    *,
    stage_version: int,
    current_inputs: dict[str, str],
) -> ResumeDecision:
    """Decide whether a stage's previous run can be reused for this run."""
    if previous_manifest is None:
        return ResumeDecision(should_skip=False, reason="no previous manifest exists")

    status = previous_manifest.get("status")
    if status != _COMPLETE_STATUS:
        return ResumeDecision(
            should_skip=False,
            reason=f"previous manifest status is {status!r}, not {_COMPLETE_STATUS!r}",
        )

    previous_stage_version = previous_manifest.get("stage_version")
    if previous_stage_version != stage_version:
        return ResumeDecision(
            should_skip=False,
            reason=(f"stage_version changed ({previous_stage_version!r} -> {stage_version!r})"),
        )

    previous_inputs = previous_manifest.get("inputs")
    if previous_inputs != current_inputs:
        return ResumeDecision(should_skip=False, reason="input fingerprints changed")

    return ResumeDecision(
        should_skip=True,
        reason="previous manifest is complete with matching stage_version and inputs",
    )
