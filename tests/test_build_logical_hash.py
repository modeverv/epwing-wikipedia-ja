from __future__ import annotations

from pathlib import Path

from wikiepwing.build_logical_hash import (
    collect_build_streams,
    compute_logical_build_hash,
    compute_stream_set_hash,
)


def test_stream_set_hash_is_order_independent() -> None:
    a = compute_stream_set_hash([("a", b"1"), ("b", b"2")])
    b = compute_stream_set_hash([("b", b"2"), ("a", b"1")])

    assert a == b


def test_stream_set_hash_is_deterministic() -> None:
    first = compute_stream_set_hash([("a", b"1")])
    second = compute_stream_set_hash([("a", b"1")])

    assert first == second


def test_stream_set_hash_differs_for_different_content() -> None:
    a = compute_stream_set_hash([("a", b"1")])
    b = compute_stream_set_hash([("a", b"2")])

    assert a != b


def test_stream_set_hash_avoids_boundary_ambiguity() -> None:
    # Without length-prefixed framing, ("ab", b"c") and ("a", b"bc") would
    # concatenate to the same bytes ("ab" + "c" == "a" + "bc" == "abc").
    a = compute_stream_set_hash([("ab", b"c")])
    b = compute_stream_set_hash([("a", b"bc")])

    assert a != b


def test_stream_set_hash_empty_input() -> None:
    assert compute_stream_set_hash([]) == compute_stream_set_hash([])


def test_collect_build_streams_includes_entries_jsonl(tmp_path: Path) -> None:
    entries = tmp_path / "entries.jsonl"
    entries.write_bytes(b'{"tag": "p1"}\n')

    streams = collect_build_streams(entries_jsonl=entries)

    assert streams == (("entries.jsonl", b'{"tag": "p1"}\n'),)


def test_collect_build_streams_includes_gaiji_and_graphics_dirs(tmp_path: Path) -> None:
    entries = tmp_path / "entries.jsonl"
    entries.write_bytes(b"e")
    gaiji_dir = tmp_path / "gaiji"
    gaiji_dir.mkdir()
    (gaiji_dir / "narrow-0001.xbm").write_bytes(b"xbm-bytes")
    graphics_dir = tmp_path / "graphics"
    graphics_dir.mkdir()
    (graphics_dir / "wiki-mark.bmp").write_bytes(b"bmp-bytes")

    streams = collect_build_streams(
        entries_jsonl=entries, gaiji_dir=gaiji_dir, graphics_dir=graphics_dir
    )

    names = {name for name, _content in streams}
    assert names == {"entries.jsonl", "gaiji/narrow-0001.xbm", "graphics/wiki-mark.bmp"}


def test_collect_build_streams_recurses_into_subdirectories(tmp_path: Path) -> None:
    entries = tmp_path / "entries.jsonl"
    entries.write_bytes(b"e")
    gaiji_dir = tmp_path / "gaiji"
    nested = gaiji_dir / "sub"
    nested.mkdir(parents=True)
    (nested / "a.xbm").write_bytes(b"x")

    streams = collect_build_streams(entries_jsonl=entries, gaiji_dir=gaiji_dir)

    names = {name for name, _content in streams}
    assert "gaiji/sub/a.xbm" in names


def test_compute_logical_build_hash_matches_manual_stream_set_hash(tmp_path: Path) -> None:
    entries = tmp_path / "entries.jsonl"
    entries.write_bytes(b"e")
    gaiji_dir = tmp_path / "gaiji"
    gaiji_dir.mkdir()
    (gaiji_dir / "a.xbm").write_bytes(b"x")

    expected = compute_stream_set_hash(
        collect_build_streams(entries_jsonl=entries, gaiji_dir=gaiji_dir)
    )
    actual = compute_logical_build_hash(entries_jsonl=entries, gaiji_dir=gaiji_dir)

    assert actual == expected


def test_compute_logical_build_hash_changes_when_a_stream_changes(tmp_path: Path) -> None:
    entries = tmp_path / "entries.jsonl"
    entries.write_bytes(b"e1")
    first = compute_logical_build_hash(entries_jsonl=entries)

    entries.write_bytes(b"e2")
    second = compute_logical_build_hash(entries_jsonl=entries)

    assert first != second


def test_compute_logical_build_hash_ignores_missing_optional_directories(tmp_path: Path) -> None:
    entries = tmp_path / "entries.jsonl"
    entries.write_bytes(b"e")

    with_none = compute_logical_build_hash(entries_jsonl=entries, gaiji_dir=None)
    without_arg = compute_logical_build_hash(entries_jsonl=entries)

    assert with_none == without_arg
