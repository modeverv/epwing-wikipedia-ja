from __future__ import annotations

import stat
from pathlib import Path

DOCKERFILE = Path("docker/toolchain.Dockerfile")
BUILD_SCRIPT = Path("docker/toolchain/build-eb.sh")
VERSION_SCRIPT = Path("docker/toolchain/version.sh")
SMOKE_SCRIPT = Path("docker/toolchain/eb-image-smoke.sh")

BASE_IMAGE = (
    "debian:bookworm-slim@sha256:60eac759739651111db372c07be67863818726f754804b8707c90979bda511df"
)
PYTHON_BASE_IMAGE = (
    "python:3.12.13-slim-bookworm@sha256:"
    "8a7e7cc04fd3e2bd787f7f24e22d5d119aa590d429b50c95dfe12b3abe52f48b"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_toolchain_uses_fixed_multistage_base_and_apt_snapshot() -> None:
    dockerfile = _read(DOCKERFILE)

    assert dockerfile.count(f"FROM {BASE_IMAGE}") == 1
    assert dockerfile.count(f"FROM {PYTHON_BASE_IMAGE}") == 1
    assert f"FROM {BASE_IMAGE} AS eb-builder" in dockerfile
    assert f"FROM {PYTHON_BASE_IMAGE} AS eb-runtime" in dockerfile
    assert "snapshot.debian.org/archive/debian/20260701T000000Z" in dockerfile
    assert "snapshot.debian.org/archive/debian-security/20260701T000000Z" in dockerfile
    assert "ARG EB_" not in dockerfile
    assert "ARG DEBIAN" not in dockerfile


def test_builder_uses_verified_lock_and_runtime_only_copies_install_tree() -> None:
    dockerfile = _read(DOCKERFILE)

    assert "COPY docker/toolchain /tmp/toolchain" in dockerfile
    assert "COPY patches/eb /tmp/patches/eb" in dockerfile
    assert "RUN /tmp/toolchain/build-eb.sh" in dockerfile
    assert "COPY --from=eb-builder /opt/eb /opt/eb" in dockerfile
    assert "PATH=/opt/venv/bin:/opt/freepwing/bin:/opt/eb/bin:" in dockerfile
    assert "LD_LIBRARY_PATH=/opt/eb/lib" in dockerfile
    assert "USER 10001:10001" in dockerfile


def test_build_and_version_scripts_keep_the_eb_boundary_explicit() -> None:
    build_script = _read(BUILD_SCRIPT)
    version_script = _read(VERSION_SCRIPT)

    assert "download-eb.sh" in build_script
    assert "tar --extract --bzip2" in build_script
    assert "./configure" in build_script
    assert "--disable-ebnet" in build_script
    assert "make" in build_script
    assert "make check" in build_script
    assert "make install" in build_script
    assert "exec ebinfo --version" in version_script

    for path in (BUILD_SCRIPT, VERSION_SCRIPT, SMOKE_SCRIPT):
        assert path.stat().st_mode & stat.S_IXUSR, f"{path} is not executable"
