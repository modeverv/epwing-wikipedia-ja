from __future__ import annotations

import stat
from pathlib import Path

FIXTURE_DIRECTORY = Path("tests/fixtures/handcrafted")
ENTRIES_PATH = FIXTURE_DIRECTORY / "entries.tsv"
PARSER_PATH = FIXTURE_DIRECTORY / "build_fixture.pl"
MAKEFILE_PATH = FIXTURE_DIRECTORY / "Makefile"
CATALOG_PATH = FIXTURE_DIRECTORY / "catalogs.txt"
SMOKE_PATH = Path("docker/toolchain/handcrafted-three-entry-smoke.sh")


def _read_entries() -> list[tuple[str, str, list[str], str, str]]:
    entries: list[tuple[str, str, list[str], str, str]] = []
    for line in ENTRIES_PATH.read_text(encoding="utf-8").splitlines():
        tag, title, aliases, body, target = line.split("\t")
        entries.append((tag, title, aliases.split("|"), body, target))
    return entries


def test_handcrafted_entries_cover_japanese_aliases_and_internal_link_cycle() -> None:
    entries = _read_entries()

    assert [(tag, title) for tag, title, _aliases, _body, _target in entries] == [
        ("emacs", "Emacs"),
        ("linux", "Linux"),
        ("wikipedia", "Wikipedia"),
    ]
    assert [target for _tag, _title, _aliases, _body, target in entries] == [
        "linux",
        "wikipedia",
        "emacs",
    ]
    assert all(len(aliases) == 2 for _tag, _title, aliases, _body, _target in entries)
    assert all(any(ord(character) > 127 for character in body) for *_, body, _target in entries)

    headwords = [
        headword
        for _tag, title, aliases, _body, _target in entries
        for headword in [title, *aliases]
    ]
    assert len(headwords) == 9
    assert len(set(headwords)) == len(headwords)
    assert {target for *_, target in entries} == {tag for tag, *_ in entries}


def test_freepwing_parser_registers_tags_references_and_all_headwords() -> None:
    parser = PARSER_PATH.read_text(encoding="utf-8")
    makefile = MAKEFILE_PATH.read_text(encoding="utf-8")
    catalog = CATALOG_PATH.read_text(encoding="utf-8")

    assert "FreePWING::FPWUtils::FPWParser" in parser
    assert "add_tag($entry->{tag})" in parser
    assert "add_reference_start()" in parser
    assert "add_reference_end($entry->{target})" in parser
    assert "for my $headword ($entry->{title}, @{$entry->{aliases}})" in parser
    assert "add_entry($headword" in parser
    assert "duplicate headword" in parser
    assert "unknown link target" in parser
    assert "include /opt/freepwing/share/freepwing/fpwutils.mk" in makefile
    assert "FPWPARSER = ./build_fixture.pl" in makefile
    assert 'Title = "手作り百科事典辞書"' in catalog
    assert 'Directory = "WIKIEP"' in catalog


def test_handcrafted_runtime_smoke_is_executable_and_wired_to_make() -> None:
    smoke = SMOKE_PATH.read_text(encoding="utf-8")
    root_makefile = Path("Makefile").read_text(encoding="utf-8")

    assert SMOKE_PATH.stat().st_mode & stat.S_IXUSR
    assert "iconv --from-code=UTF-8 --to-code=EUC-JP" in smoke
    assert smoke.count("fpwmake") >= 2
    assert "ebinfo" in smoke
    assert "the number of subbooks: 1" in smoke
    assert "directory: wikiep" in smoke
    assert "test-handcrafted:" in root_makefile
    assert "sh docker/toolchain/handcrafted-three-entry-smoke.sh" in root_makefile
