from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

LOCK_PATH = Path("docker/toolchain/eb-source.env")
FETCH_SCRIPT = Path("docker/toolchain/fetch-verified.sh")
DOWNLOAD_SCRIPT = Path("docker/toolchain/download-eb.sh")


def _read_lock() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        assert separator == "=", line
        assert name.startswith("EB_"), name
        values[name] = value.strip("'\"")
    return values


def _run_fetch(
    source: Path, expected_sha256: str, expected_size: int, destination: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "sh",
            str(FETCH_SCRIPT),
            "--local-file",
            str(source),
            expected_sha256,
            str(expected_size),
            str(destination),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_eb_source_is_pinned_to_official_release() -> None:
    lock = _read_lock()

    assert lock == {
        "EB_VERSION": "4.4.3",
        "EB_SOURCE_FILENAME": "eb-4.4.3.tar.bz2",
        "EB_SOURCE_URL": (
            "https://github.com/mistydemeo/eb/releases/download/v4.4.3/eb-4.4.3.tar.bz2"
        ),
        "EB_SOURCE_SHA256": "abe710a77c6fc3588232977bb2f30a2e69ddfbe9fa8d0b05b0d67d95e36f4b5f",
        "EB_SOURCE_SIZE_BYTES": "505510",
    }


def test_verified_fetch_publishes_valid_local_source_atomically(tmp_path: Path) -> None:
    source = tmp_path / "source.tar.bz2"
    source.write_bytes(b"verified source fixture\n")
    expected_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    destination = tmp_path / "nested" / "source.tar.bz2"

    result = _run_fetch(source, expected_sha256, source.stat().st_size, destination)

    assert result.returncode == 0, result.stderr
    assert destination.read_bytes() == source.read_bytes()
    assert result.stdout.strip() == str(destination)
    assert list(destination.parent.glob("*.part.*")) == []


def test_verified_fetch_rejects_checksum_mismatch_without_artifact(tmp_path: Path) -> None:
    source = tmp_path / "source.tar.bz2"
    source.write_bytes(b"tampered source\n")
    destination = tmp_path / "source.out"

    result = _run_fetch(source, "0" * 64, source.stat().st_size, destination)

    assert result.returncode != 0
    assert "SHA-256 mismatch" in result.stderr
    assert "expected=" + "0" * 64 in result.stderr
    assert "actual=" + hashlib.sha256(source.read_bytes()).hexdigest() in result.stderr
    assert not destination.exists()
    assert list(tmp_path.glob("*.part.*")) == []


def test_verified_fetch_rejects_size_mismatch_before_publish(tmp_path: Path) -> None:
    source = tmp_path / "source.tar.bz2"
    source.write_bytes(b"unexpected size\n")
    destination = tmp_path / "source.out"
    expected_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()

    result = _run_fetch(source, expected_sha256, source.stat().st_size + 1, destination)

    assert result.returncode != 0
    assert "size mismatch" in result.stderr
    assert not destination.exists()


def test_eb_download_wrapper_enforces_locked_checksum_for_local_mirror(tmp_path: Path) -> None:
    local_mirror = tmp_path / "eb-4.4.3.tar.bz2"
    local_mirror.write_bytes(b"not the pinned EB source\n")
    destination = tmp_path / "downloads" / "eb-4.4.3.tar.bz2"

    result = subprocess.run(
        ["sh", str(DOWNLOAD_SCRIPT), str(destination), str(local_mirror)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "mismatch" in result.stderr
    assert not destination.exists()
