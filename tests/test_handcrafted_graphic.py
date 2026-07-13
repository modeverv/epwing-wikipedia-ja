from __future__ import annotations

import struct
import subprocess
from pathlib import Path

FIXTURE_DIRECTORY = Path("tests/fixtures/handcrafted")
GENERATOR_PATH = FIXTURE_DIRECTORY / "generate_bitmap.pl"
CGRAPHS_PATH = FIXTURE_DIRECTORY / "cgraphs.txt"
PARSER_PATH = FIXTURE_DIRECTORY / "build_fixture.pl"
MAKEFILE_PATH = FIXTURE_DIRECTORY / "Makefile"
SMOKE_PATH = Path("docker/toolchain/handcrafted-three-entry-smoke.sh")


def _generate_bitmap(path: Path) -> bytes:
    subprocess.run(["perl", str(GENERATOR_PATH), str(path)], check=True)
    return path.read_bytes()


def test_generated_bitmap_is_deterministic_small_uncompressed_24_bit_bmp(
    tmp_path: Path,
) -> None:
    first = _generate_bitmap(tmp_path / "first.bmp")
    second = _generate_bitmap(tmp_path / "second.bmp")

    assert first == second
    assert len(first) == 70
    assert first[:2] == b"BM"
    assert struct.unpack_from("<I", first, 2)[0] == len(first)
    assert struct.unpack_from("<I", first, 10)[0] == 54
    assert struct.unpack_from("<IiiHHII", first, 14) == (40, 2, 2, 1, 24, 0, 16)


def test_freepwing_definition_registers_one_bitmap_and_wikipedia_reference() -> None:
    cgraphs = CGRAPHS_PATH.read_text(encoding="ascii").splitlines()
    parser = PARSER_PATH.read_text(encoding="utf-8")
    makefile = MAKEFILE_PATH.read_text(encoding="utf-8")

    assert cgraphs == ["wiki-mark bitmap.bmp"]
    assert "CGRAPHS = cgraphs.txt" in makefile
    assert 'if ($entry->{tag} eq "wikipedia")' in parser
    assert 'add_color_graphic_start("wiki-mark")' in parser
    assert "add_color_graphic_end()" in parser


def test_runtime_smoke_generates_and_verifies_embedded_bitmap() -> None:
    smoke = SMOKE_PATH.read_text(encoding="utf-8")

    assert "generate_bitmap.pl" in smoke
    assert "work/cgr" in smoke
    assert "invalid color graphic record" in smoke
    assert "missing BMP payload in HONMON" in smoke
    assert 'grep -F "directory: wikiep"' in smoke
