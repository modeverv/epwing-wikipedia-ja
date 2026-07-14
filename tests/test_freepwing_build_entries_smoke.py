from __future__ import annotations

from pathlib import Path

SMOKE_SCRIPT = Path("docker/toolchain/freepwing-build-entries-smoke.sh")
DRIVER_SCRIPT = Path("docker/toolchain/freepwing_build_entries.pl")


def test_smoke_script_and_driver_exist_and_are_wired() -> None:
    assert SMOKE_SCRIPT.is_file()
    assert DRIVER_SCRIPT.is_file()


def test_smoke_script_uses_the_python_writer_and_generic_driver() -> None:
    content = SMOKE_SCRIPT.read_text(encoding="utf-8")

    assert "write_entries_jsonl" in content
    assert "freepwing_build_entries.pl" in content
    assert "wikiepwing-eb-search" in content


def test_driver_script_reads_json_lines_and_encodes_euc_jp() -> None:
    content = DRIVER_SCRIPT.read_text(encoding="utf-8")

    assert "JSON::PP" in content
    assert "euc-jp" in content
    assert "entries.jsonl" in content
    assert "initialize_fpwparser" in content
    assert "finalize_fpwparser" in content


def test_driver_script_rejects_unknown_link_targets() -> None:
    content = DRIVER_SCRIPT.read_text(encoding="utf-8")

    assert "unknown link target" in content


def test_driver_script_rejects_duplicate_headwords_across_entries() -> None:
    content = DRIVER_SCRIPT.read_text(encoding="utf-8")

    assert "duplicate headword" in content
