from __future__ import annotations

import stat
from pathlib import Path

PACKAGE_SCRIPT = Path("docker/toolchain/package-smoke.sh")


def test_runtime_has_fixed_zip_and_package_script_is_wired() -> None:
    dockerfile = Path("docker/toolchain.Dockerfile").read_text(encoding="utf-8")
    script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "zip=3.0-13" in dockerfile
    assert PACKAGE_SCRIPT.stat().st_mode & stat.S_IXUSR
    assert "toolchain-smoke.epwing.zip" in script
    assert "handcrafted-three-entry-smoke.sh" in script
    assert "package-toolchain:" in makefile
    assert "docker/toolchain/package-smoke.sh" in makefile


def test_package_flow_compresses_probes_and_validates_zip_members() -> None:
    smoke = Path("docker/toolchain/handcrafted-three-entry-smoke.sh").read_text(encoding="utf-8")
    package = PACKAGE_SCRIPT.read_text(encoding="utf-8")

    assert "ebzip --level 0" in smoke
    assert "toolchain-capabilities-ebzip.json" in smoke
    assert "cmp /probe-output/toolchain-capabilities.json" in smoke
    assert "zip -X" in smoke
    assert "zipfile.ZipFile" in package
    assert "WIKIEP/DATA/HONMON.ebz" in package
    assert "WIKIEP/GAIJI/GA16HALF.ebz" in package
    assert "WIKIEP/GAIJI/GA16FULL.ebz" in package
    assert "is_symlink" in package
