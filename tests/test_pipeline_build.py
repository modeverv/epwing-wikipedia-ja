from __future__ import annotations

import pytest

from wikiepwing.pipeline.build import BuildPlanError, is_forced_stage, stages_from


def test_stages_from_none_returns_full_order() -> None:
    assert stages_from(None) == ("ingest", "normalize", "generate")


def test_stages_from_middle_stage_skips_earlier_stages() -> None:
    assert stages_from("normalize") == ("normalize", "generate")


def test_stages_from_last_stage_returns_single_stage() -> None:
    assert stages_from("generate") == ("generate",)


def test_stages_from_unknown_stage_raises() -> None:
    with pytest.raises(BuildPlanError):
        stages_from("nonexistent")


def test_is_forced_stage_none_forces_nothing() -> None:
    assert is_forced_stage("ingest", None) is False
    assert is_forced_stage("normalize", None) is False


def test_is_forced_stage_matches_only_named_stage() -> None:
    assert is_forced_stage("normalize", "normalize") is True
    assert is_forced_stage("ingest", "normalize") is False
    assert is_forced_stage("generate", "normalize") is False


def test_is_forced_stage_unknown_stage_raises() -> None:
    with pytest.raises(BuildPlanError):
        is_forced_stage("ingest", "nonexistent")
