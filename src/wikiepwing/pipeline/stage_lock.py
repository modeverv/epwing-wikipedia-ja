"""Stage lock (TASK-I003, ARCHITECTURE.md 7.2 Orchestrator responsibility "lock取得").

A manifest's `status` field alone isn't a real mutex: reading "not running"
and then starting a run races against another process doing the same thing
concurrently. `acquire_stage_lock` uses an OS-level advisory lock
(`fcntl.flock`) to guarantee only one process runs a given stage at a time.
POSIX-only, matching this project's Docker/Linux-only execution model.
"""

from __future__ import annotations

import fcntl
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class StageLockError(RuntimeError):
    """Raised when a stage lock is already held by another process."""


@contextmanager
def acquire_stage_lock(lock_path: Path) -> Iterator[None]:
    """Acquire an exclusive advisory lock at `lock_path` for the duration of the `with` block."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("w")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise StageLockError(
                f"stage lock {lock_path} is already held by another process"
            ) from error
        handle.write(str(os.getpid()))
        handle.flush()
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()
