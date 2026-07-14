from __future__ import annotations

from wikiepwing.pipeline.resume import decide_resume

_INPUTS = {"source_lock": "sha256:abc"}


def test_no_previous_manifest_requires_run() -> None:
    decision = decide_resume(None, stage_version=1, current_inputs=_INPUTS)

    assert decision.should_skip is False
    assert "no previous manifest" in decision.reason


def test_previous_manifest_not_complete_requires_run() -> None:
    previous = {"status": "failed", "stage_version": 1, "inputs": _INPUTS}

    decision = decide_resume(previous, stage_version=1, current_inputs=_INPUTS)

    assert decision.should_skip is False
    assert "failed" in decision.reason


def test_previous_manifest_running_requires_run() -> None:
    previous = {"status": "running", "stage_version": 1, "inputs": _INPUTS}

    decision = decide_resume(previous, stage_version=1, current_inputs=_INPUTS)

    assert decision.should_skip is False


def test_stage_version_mismatch_requires_run() -> None:
    previous = {"status": "complete", "stage_version": 1, "inputs": _INPUTS}

    decision = decide_resume(previous, stage_version=2, current_inputs=_INPUTS)

    assert decision.should_skip is False
    assert "stage_version" in decision.reason


def test_inputs_mismatch_requires_run() -> None:
    previous = {"status": "complete", "stage_version": 1, "inputs": _INPUTS}
    changed_inputs = {"source_lock": "sha256:different"}

    decision = decide_resume(previous, stage_version=1, current_inputs=changed_inputs)

    assert decision.should_skip is False
    assert "input" in decision.reason


def test_matching_complete_manifest_can_be_skipped() -> None:
    previous = {"status": "complete", "stage_version": 1, "inputs": _INPUTS}

    decision = decide_resume(previous, stage_version=1, current_inputs=_INPUTS)

    assert decision.should_skip is True


def test_extra_inputs_key_counts_as_mismatch() -> None:
    previous = {"status": "complete", "stage_version": 1, "inputs": _INPUTS}
    extra_inputs = {**_INPUTS, "config": "sha256:extra"}

    decision = decide_resume(previous, stage_version=1, current_inputs=extra_inputs)

    assert decision.should_skip is False
