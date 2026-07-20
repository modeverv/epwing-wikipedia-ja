from __future__ import annotations

from pathlib import Path

SMOKE_SCRIPT = Path("docker/toolchain/freepwing-build-entries-smoke.sh")
DRIVER_SCRIPT = Path("docker/toolchain/freepwing_build_entries.pl")


def test_smoke_script_and_driver_exist_and_are_wired() -> None:
    assert SMOKE_SCRIPT.is_file()
    assert DRIVER_SCRIPT.is_file()


def test_smoke_script_uses_the_python_writer_and_generic_driver() -> None:
    content = SMOKE_SCRIPT.read_text(encoding="utf-8")

    assert "write_entries_jsonl_stream" in content
    assert "freepwing_build_entries.pl" in content
    assert "wikiepwing-eb-search" in content
    assert "headwords skipped reason=word-is-empty count=1" in content


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


def test_driver_script_renders_references_inline_not_at_entry_end() -> None:
    content = DRIVER_SCRIPT.read_text(encoding="utf-8")

    assert "REF_TOKEN" in content
    assert "inline reference target not declared" in content
    assert "add_reference_start" in content
    assert "add_reference_end" in content
    assert "for my $target (@{$entry->{targets}})" not in content


def test_driver_script_renders_color_graphics_at_body_position() -> None:
    content = DRIVER_SCRIPT.read_text(encoding="utf-8")

    assert "GRAPHIC_TOKEN" in content
    assert "add_color_graphic_start" in content
    assert "add_color_graphic_end" in content
    assert 'GraphicRenderNode(name="wiki-mark")' in SMOKE_SCRIPT.read_text(encoding="utf-8")


def test_driver_script_counts_duplicate_headwords_across_entries() -> None:
    content = DRIVER_SCRIPT.read_text(encoding="utf-8")

    assert "headwords duplicated count=" in content


def test_driver_script_reports_backend_empty_headwords_and_continues() -> None:
    content = DRIVER_SCRIPT.read_text(encoding="utf-8")

    assert "sub is_empty_search_word" in content
    assert "if (is_empty_search_word($headword))" in content
    assert content.index("if (is_empty_search_word($headword))") < content.index(
        "$duplicate_headwords++"
    )
    assert "headword skipped tag=" in content
    assert "headwords skipped reason=word-is-empty count=" in content


def test_driver_script_parallelizes_parsing_and_prefers_json_xs() -> None:
    content = DRIVER_SCRIPT.read_text(encoding="utf-8")

    assert "JSON::XS" in content
    assert "WIKIEPWING_PARSE_JOBS" in content
    assert "fork" in content
