from __future__ import annotations

import subprocess
from pathlib import Path

LOCK_PATH = Path("docker/toolchain/freepwing-source.env")
DOWNLOAD_SCRIPT = Path("docker/toolchain/download-freepwing.sh")
PATCH_DIRECTORY = Path("patches/freepwing")


def _read_lock() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        assert separator == "=", line
        assert name.startswith("FREEPWING_"), name
        values[name] = value.strip("'\"")
    return values


def test_freepwing_source_is_pinned_to_latest_upstream_release() -> None:
    lock = _read_lock()

    assert lock == {
        "FREEPWING_VERSION": "1.6.1",
        "FREEPWING_SOURCE_FILENAME": "freepwing_1.6.1.orig.tar.bz2",
        "FREEPWING_SOURCE_URL": (
            "https://deb.debian.org/debian/pool/main/f/freepwing/freepwing_1.6.1.orig.tar.bz2"
        ),
        "FREEPWING_SOURCE_SHA256": (
            "274a8cf392e2c46662bcf3eedce331fe84e65f7e5e6044d0178b2150a0704fc2"
        ),
        "FREEPWING_SOURCE_SIZE_BYTES": "119373",
        "FREEPWING_SOURCE_ROOT": "freepwing-1.6.1",
    }


def test_freepwing_download_wrapper_enforces_locked_source(tmp_path: Path) -> None:
    local_mirror = tmp_path / "freepwing_1.6.1.orig.tar.bz2"
    local_mirror.write_bytes(b"not the pinned FreePWING source\n")
    destination = tmp_path / "downloads" / "freepwing_1.6.1.orig.tar.bz2"

    result = subprocess.run(
        ["sh", str(DOWNLOAD_SCRIPT), str(destination), str(local_mirror)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "mismatch" in result.stderr
    assert not destination.exists()


def test_freepwing_patch_directory_has_an_explicit_policy() -> None:
    readme = (PATCH_DIRECTORY / "README.md").read_text(encoding="utf-8")

    assert "FreePWING 1.6.1" in readme
    assert "TASK-B004" in readme
    assert "patch -p1" in readme
    assert list(PATCH_DIRECTORY.glob("*.patch")) == []
