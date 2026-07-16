from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from wikiepwing.clean import clean_old_runs, find_removable_runs


def _make_run(runs_dir: Path, name: str, *, mtime_offset: float) -> Path:
    run_dir = runs_dir / name
    run_dir.mkdir(parents=True)
    (run_dir / "manifests").mkdir()
    (run_dir / "manifests" / "40-normalize.json").write_bytes(b"{}")
    now = time.time()
    os.utime(run_dir, (now + mtime_offset, now + mtime_offset))
    return run_dir


def test_missing_runs_dir_returns_empty(tmp_path: Path) -> None:
    assert find_removable_runs(tmp_path / "runs", keep_runs=2) == ()


def test_rejects_negative_keep_runs(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="keep_runs"):
        find_removable_runs(tmp_path, keep_runs=-1)


def test_keeps_the_newest_runs(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    old_run = _make_run(runs_dir, "run-old", mtime_offset=-200)
    mid_run = _make_run(runs_dir, "run-mid", mtime_offset=-100)
    new_run = _make_run(runs_dir, "run-new", mtime_offset=0)

    removable = find_removable_runs(runs_dir, keep_runs=2)

    assert removable == (old_run,)
    assert mid_run not in removable
    assert new_run not in removable


def test_keep_runs_zero_removes_everything(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    _make_run(runs_dir, "run-a", mtime_offset=-10)
    _make_run(runs_dir, "run-b", mtime_offset=0)

    removable = find_removable_runs(runs_dir, keep_runs=0)

    assert len(removable) == 2


def test_keep_runs_larger_than_available_removes_nothing(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    _make_run(runs_dir, "run-a", mtime_offset=0)

    removable = find_removable_runs(runs_dir, keep_runs=5)

    assert removable == ()


def test_dry_run_does_not_delete_anything(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    old_run = _make_run(runs_dir, "run-old", mtime_offset=-100)
    _make_run(runs_dir, "run-new", mtime_offset=0)

    removed = clean_old_runs(runs_dir, keep_runs=1, dry_run=True)

    assert removed == (old_run,)
    assert old_run.is_dir()


def test_clean_old_runs_actually_deletes(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    old_run = _make_run(runs_dir, "run-old", mtime_offset=-100)
    new_run = _make_run(runs_dir, "run-new", mtime_offset=0)

    removed = clean_old_runs(runs_dir, keep_runs=1, dry_run=False)

    assert removed == (old_run,)
    assert not old_run.exists()
    assert new_run.is_dir()


def test_clean_old_runs_never_touches_a_different_directory(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    _make_run(runs_dir, "run-old", mtime_offset=-100)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "jawiki-lite.epwing.zip").write_bytes(b"zip-bytes")

    clean_old_runs(runs_dir, keep_runs=0, dry_run=False)

    assert (output_dir / "jawiki-lite.epwing.zip").is_file()
