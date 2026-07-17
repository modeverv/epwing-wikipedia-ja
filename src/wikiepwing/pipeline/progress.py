"""Shared progress event for heavyweight pipeline work outside record loops."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PhaseProgress:
    """One bounded-progress update for a named pipeline phase."""

    phase: str
    completed: int
    total: int | None
    unit: str
    complete: bool = False


def fingerprint_progress_callback(
    callback: Callable[[PhaseProgress], None] | None, phase: str
) -> Callable[[int, int], None] | None:
    """Adapt byte fingerprint progress to a named pipeline phase."""
    if callback is None:
        return None

    def report(completed: int, total: int) -> None:
        callback(
            PhaseProgress(
                phase=phase,
                completed=completed,
                total=total,
                unit="bytes",
                complete=completed >= total,
            )
        )

    return report
