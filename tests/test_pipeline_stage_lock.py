from __future__ import annotations

import os
from pathlib import Path

import pytest

from wikiepwing.pipeline.stage_lock import StageLockError, acquire_stage_lock


def test_acquire_stage_lock_succeeds(tmp_path: Path) -> None:
    lock_path = tmp_path / "stage.lock"

    with acquire_stage_lock(lock_path):
        assert lock_path.is_file()


def test_acquire_stage_lock_writes_pid(tmp_path: Path) -> None:
    lock_path = tmp_path / "stage.lock"

    with acquire_stage_lock(lock_path):
        assert lock_path.read_text(encoding="utf-8") == str(os.getpid())


def test_second_acquire_while_held_raises(tmp_path: Path) -> None:
    lock_path = tmp_path / "stage.lock"

    with acquire_stage_lock(lock_path):
        with pytest.raises(StageLockError, match="already held"):
            with acquire_stage_lock(lock_path):
                pass


def test_lock_is_released_after_context_exits(tmp_path: Path) -> None:
    lock_path = tmp_path / "stage.lock"

    with acquire_stage_lock(lock_path):
        pass

    with acquire_stage_lock(lock_path):
        assert lock_path.is_file()


def test_lock_is_released_when_body_raises(tmp_path: Path) -> None:
    lock_path = tmp_path / "stage.lock"

    with pytest.raises(RuntimeError, match="boom"):
        with acquire_stage_lock(lock_path):
            raise RuntimeError("boom")

    with acquire_stage_lock(lock_path):
        assert lock_path.is_file()


def test_acquire_stage_lock_creates_parent_directories(tmp_path: Path) -> None:
    lock_path = tmp_path / "nested" / "dir" / "stage.lock"

    with acquire_stage_lock(lock_path):
        assert lock_path.is_file()
