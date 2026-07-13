from __future__ import annotations

import stat
from pathlib import Path

SMOKE_SCRIPT = Path("docker/toolchain/ebzip-roundtrip-smoke.sh")
MAKEFILE = Path("Makefile")


def test_ebzip_smoke_defines_a_deterministic_epwing_roundtrip() -> None:
    script = SMOKE_SCRIPT.read_text(encoding="utf-8")

    assert "command -v ebzip" in script
    assert "command -v ebunzip" in script
    assert "command -v ebzipinfo" in script
    assert "ebzip (EB Library) version 4.4.3" in script
    assert "chr(0) x 2048" in script
    assert '"ROUNDTRP"' in script
    assert "--level 0" in script
    assert "HONMON.ebz" in script
    assert "ebzipinfo" in script
    assert "ebunzip" in script
    assert script.count("cmp ") == 2


def test_ebzip_smoke_is_executable_and_has_a_make_target() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")

    assert SMOKE_SCRIPT.stat().st_mode & stat.S_IXUSR
    assert "test-ebzip:" in makefile
    assert "sh docker/toolchain/ebzip-roundtrip-smoke.sh" in makefile
