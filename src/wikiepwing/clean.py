"""Safe clean command (TASK-S008, PLAN.md 29's `wikiepwing clean --keep-runs 2`).

Only targets `paths.work/runs/<run-id>/` -- the intermediate stage
manifests/working state each pipeline run leaves behind -- never
`paths.output`'s packaged artifacts, matching 29's exit condition "old
outputを自動削除しない" (never auto-delete old output). Runs are kept by
most-recently-modified, not by any naming convention, so this works
regardless of how a run_id was generated.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def find_removable_runs(runs_dir: Path, *, keep_runs: int) -> tuple[Path, ...]:
    """Return the run directories under `runs_dir` to remove, keeping the newest `keep_runs`."""
    if keep_runs < 0:
        raise ValueError("keep_runs must not be negative")
    if not runs_dir.is_dir():
        return ()

    runs = sorted(
        (path for path in runs_dir.iterdir() if path.is_dir()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return tuple(runs[keep_runs:])


def clean_old_runs(runs_dir: Path, *, keep_runs: int, dry_run: bool = False) -> tuple[Path, ...]:
    """Remove old run directories under `runs_dir`, returning what was (or would be) removed."""
    removable = find_removable_runs(runs_dir, keep_runs=keep_runs)
    if not dry_run:
        for run_dir in removable:
            if run_dir.is_symlink():
                raise ValueError(f"run directory must not be a symlink: {run_dir}")
            shutil.rmtree(run_dir)
    return removable
