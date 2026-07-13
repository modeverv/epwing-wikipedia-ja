from __future__ import annotations

import re
import subprocess
from pathlib import Path

FIXTURE_DIRECTORY = Path("tests/fixtures/handcrafted")
GENERATOR_PATH = FIXTURE_DIRECTORY / "generate_gaiji.pl"
MAKEFILE_PATH = FIXTURE_DIRECTORY / "Makefile"
PARSER_PATH = FIXTURE_DIRECTORY / "build_fixture.pl"
CATALOG_PATH = FIXTURE_DIRECTORY / "catalogs.txt"
SMOKE_PATH = Path("docker/toolchain/handcrafted-three-entry-smoke.sh")


def _generate_gaiji(tmp_path: Path) -> tuple[str, str]:
    half_path = tmp_path / "half16.xbm"
    full_path = tmp_path / "full16.xbm"
    subprocess.run(["perl", str(GENERATOR_PATH), str(half_path), str(full_path)], check=True)
    return (
        half_path.read_text(encoding="ascii"),
        full_path.read_text(encoding="ascii"),
    )


def _xbm_bytes(source: str) -> list[int]:
    return [int(value, 16) for value in re.findall(r"0x([0-9a-f]{2})", source)]


def test_generator_creates_deterministic_narrow_and_wide_16_dot_xbm(
    tmp_path: Path,
) -> None:
    first = _generate_gaiji(tmp_path)
    second = _generate_gaiji(tmp_path)

    assert first == second
    assert "#define half_width 8" in first[0]
    assert "#define half_height 16" in first[0]
    assert "#define full_width 16" in first[1]
    assert "#define full_height 16" in first[1]
    assert len(_xbm_bytes(first[0])) == 16
    assert len(_xbm_bytes(first[1])) == 32
    assert any(_xbm_bytes(first[0]))
    assert any(_xbm_bytes(first[1]))


def test_freepwing_registers_and_references_one_narrow_and_one_wide_gaiji() -> None:
    makefile = MAKEFILE_PATH.read_text(encoding="utf-8")
    parser = PARSER_PATH.read_text(encoding="utf-8")
    catalog = CATALOG_PATH.read_text(encoding="utf-8")

    assert (FIXTURE_DIRECTORY / "halfchars.txt").read_text(encoding="ascii") == (
        "half-mark half16.xbm\n"
    )
    assert (FIXTURE_DIRECTORY / "fullchars.txt").read_text(encoding="ascii") == (
        "full-mark full16.xbm\n"
    )
    assert "HALFCHARS = halfchars.txt" in makefile
    assert "FULLCHARS = fullchars.txt" in makefile
    assert 'if ($entry->{tag} eq "linux")' in parser
    assert 'add_half_user_character("half-mark") or die' in parser
    assert 'add_full_user_character("full-mark") or die' in parser
    assert 'HanGaiji = "GA16HALF"' in catalog
    assert 'ZenGaiji = "GA16FULL"' in catalog


def test_runtime_smoke_stages_both_gaiji_files_for_eb_library() -> None:
    smoke = SMOKE_PATH.read_text(encoding="utf-8")

    assert "generate_gaiji.pl" in smoke
    assert 'test "$(wc -c < gai16h' in smoke
    assert 'test "$(wc -c < gai16f' in smoke
    assert "GAIJI/GA16HALF" in smoke
    assert "GAIJI/GA16FULL" in smoke
    assert 'grep -F "font sizes: 16"' in smoke
    assert 'grep -F "narrow font characters: 0xa121 -- 0xa121"' in smoke
    assert 'grep -F "wide font characters: 0xa121 -- 0xa121"' in smoke
