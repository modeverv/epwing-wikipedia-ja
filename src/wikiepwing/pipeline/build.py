"""Multi-stage build plan (TASK-I006, PLAN.md Phase 9 `--from-stage`/`--force-stage`).

Pure stage-selection logic for `wikiepwing build`, which chains the ingest,
normalize, and generate stages. Each stage's own `run_*` function already
decides for itself whether it can reuse a previous complete run
(`wikiepwing.pipeline.resume.decide_resume`); this module only decides
*which* stages the build command attempts and which single stage (if any)
should have its own resume-reuse bypassed.
"""

from __future__ import annotations

STAGE_ORDER: tuple[str, ...] = ("ingest", "normalize", "generate")


class BuildPlanError(ValueError):
    """Raised when `--from-stage`/`--force-stage` name an unknown stage."""


def stages_from(from_stage: str | None) -> tuple[str, ...]:
    """Return the stages to attempt, starting at (and including) `from_stage`.

    Earlier stages are assumed already complete and are not attempted at all.
    Returns the full `STAGE_ORDER` when `from_stage` is None.
    """
    if from_stage is None:
        return STAGE_ORDER
    if from_stage not in STAGE_ORDER:
        raise BuildPlanError(f"unknown stage {from_stage!r}; must be one of {STAGE_ORDER}")
    index = STAGE_ORDER.index(from_stage)
    return STAGE_ORDER[index:]


def is_forced_stage(stage: str, force_stage: str | None) -> bool:
    """Return whether `stage` should bypass its own resume-reuse decision."""
    if force_stage is None:
        return False
    if force_stage not in STAGE_ORDER:
        raise BuildPlanError(f"unknown stage {force_stage!r}; must be one of {STAGE_ORDER}")
    return stage == force_stage
