"""Resume decision (TASK-I005/I007, ARCHITECTURE.md 7.2 "manifest比較"/"resume判定").

A stage's previous manifest can be *reused* (the stage skipped entirely)
only when all of the following hold: a previous manifest exists, it
finished with status "complete", its `stage_version` matches the stage's
current version, its recorded `inputs` fingerprints match the inputs
computed for the current run, and (when the caller supplies one) its
recorded output fingerprint still matches the output file actually on
disk. Any mismatch means the previous outputs are stale, missing, or
corrupt, and the stage must run again (PLAN.md Phase 9 "corrupt output
再利用拒否").

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
    current_output_fingerprint: tuple[int, str] | None = None,
) -> ResumeDecision:
    """Decide whether a stage's previous run can be reused for this run.

    `current_output_fingerprint` is the `(size_bytes, sha256)` of the stage's
    actual output file on disk right now, or None if that file is currently
    missing. If the previous manifest recorded an output, this check is
    fail-closed: a missing file, or a mismatch, means the previous run cannot
    be trusted even though its manifest says "complete" (the file was deleted
    or corrupted since). Callers with a manifest that recorded no outputs
    (or an empty `outputs` list) skip this check regardless of what they pass.
    """
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

    previous_outputs = previous_manifest.get("outputs")
    if isinstance(previous_outputs, list) and previous_outputs:
        first_output = previous_outputs[0]
        if isinstance(first_output, dict):
            expected = (first_output.get("size_bytes"), first_output.get("sha256"))
            if current_output_fingerprint is None:
                return ResumeDecision(should_skip=False, reason="previous output file is missing")
            if current_output_fingerprint != expected:
                return ResumeDecision(
                    should_skip=False,
                    reason="previous output file no longer matches the manifest "
                    "(corrupt or modified)",
                )

    return ResumeDecision(
        should_skip=True,
        reason="previous manifest is complete with matching stage_version, inputs, and outputs",
    )
