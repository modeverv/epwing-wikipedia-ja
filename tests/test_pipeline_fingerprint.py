from __future__ import annotations

from pathlib import Path

from wikiepwing.pipeline.fingerprint import compute_input_fingerprint


def test_compute_input_fingerprint_has_sha256_prefix(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_bytes(b"hello")

    fingerprint = compute_input_fingerprint(path)

    assert fingerprint.startswith("sha256:")
    assert len(fingerprint) == len("sha256:") + 64


def test_compute_input_fingerprint_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_bytes(b"hello")

    assert compute_input_fingerprint(path) == compute_input_fingerprint(path)


def test_compute_input_fingerprint_changes_with_content(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_bytes(b"hello")
    first = compute_input_fingerprint(path)

    path.write_bytes(b"world")
    second = compute_input_fingerprint(path)

    assert first != second


def test_compute_input_fingerprint_matches_known_sha256(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_bytes(b"")

    fingerprint = compute_input_fingerprint(path)

    assert fingerprint == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
