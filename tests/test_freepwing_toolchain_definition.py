from __future__ import annotations

import stat
from pathlib import Path

DOCKERFILE = Path("docker/toolchain.Dockerfile")
BUILD_SCRIPT = Path("docker/toolchain/build-freepwing.sh")
VERSION_SCRIPT = Path("docker/toolchain/version.sh")
SMOKE_SCRIPT = Path("docker/toolchain/eb-image-smoke.sh")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_builder_uses_verified_freepwing_source_and_fixed_install_tree() -> None:
    dockerfile = _read(DOCKERFILE)
    build_script = _read(BUILD_SCRIPT)

    assert "perl=5.36.0-7+deb12u3" in dockerfile
    assert "COPY patches/freepwing /tmp/patches/freepwing" in dockerfile
    assert "RUN /tmp/toolchain/build-freepwing.sh" in dockerfile
    assert "download-freepwing.sh" in build_script
    assert "FREEPWING_SOURCE_ROOT" in build_script
    assert "tar --list --bzip2" in build_script
    assert "--strip-components=1" in build_script
    assert "--with-perllibdir=/opt/freepwing/lib/perl5" in build_script
    assert "find /tmp/patches/freepwing" in build_script
    assert "LC_ALL=C sort" in build_script
    assert "patch --directory" in build_script
    assert "make check" in build_script
    assert "make install" in build_script


def test_runtime_contains_only_pinned_required_freepwing_dependencies() -> None:
    dockerfile = _read(DOCKERFILE)

    assert "make=4.3-4.1" in dockerfile
    assert dockerfile.count("perl=5.36.0-7+deb12u3") == 2
    assert "COPY --from=eb-builder /opt/freepwing /opt/freepwing" in dockerfile
    assert "PERL5LIB=/opt/freepwing/lib/perl5" in dockerfile
    assert "PATH=/opt/venv/bin:/opt/freepwing/bin:/opt/eb/bin:" in dockerfile
    assert "io.wikiepwing.freepwing.source.sha256=" in dockerfile
    assert "ARG FREEPWING_" not in dockerfile


def test_version_and_smoke_scripts_cover_freepwing_runtime() -> None:
    version_script = _read(VERSION_SCRIPT)
    smoke_script = _read(SMOKE_SCRIPT)

    assert "freepwing-source.env" in version_script
    assert "FreePWING %s" in version_script
    assert "command -v fpwmake" in smoke_script
    assert "FreePWING::Text" in smoke_script
    assert "FreePWING::Link::GDBM" in smoke_script
    assert "FreePWING::Link::BDB" in smoke_script
    assert "command -v gmake" in smoke_script
    assert "test ! -e /tmp/freepwing-build" in smoke_script

    for path in (BUILD_SCRIPT, VERSION_SCRIPT, SMOKE_SCRIPT):
        assert path.stat().st_mode & stat.S_IXUSR, f"{path} is not executable"
