from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest

from wikiepwing.ingest.tar_reader import TarStreamError, iter_ndjson_lines

FIXTURE_NDJSON = Path("tests/fixtures/enterprise/normal_articles.ndjson")


def _make_tar_gz(path: Path, *, member_name: str, body: bytes) -> None:
    with tarfile.open(path, mode="w:gz") as archive:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(body)
        archive.addfile(info, io.BytesIO(body))


def test_streams_all_lines_from_real_fixture_content(tmp_path: Path) -> None:
    body = FIXTURE_NDJSON.read_bytes()
    tar_path = tmp_path / "chunk_0.tar.gz"
    _make_tar_gz(tar_path, member_name="chunk_0.ndjson", body=body)

    lines = list(iter_ndjson_lines(tar_path))

    expected_lines = [line for line in body.splitlines() if line.strip()]
    assert lines == expected_lines
    assert len(lines) == 10
    assert json.loads(lines[0])["name"] == "Emacs"


def test_skips_blank_lines(tmp_path: Path) -> None:
    tar_path = tmp_path / "chunk_0.tar.gz"
    _make_tar_gz(tar_path, member_name="chunk_0.ndjson", body=b'{"a":1}\n\n{"a":2}\n')

    lines = list(iter_ndjson_lines(tar_path))

    assert lines == [b'{"a":1}', b'{"a":2}']


def test_handles_final_line_without_trailing_newline(tmp_path: Path) -> None:
    tar_path = tmp_path / "chunk_0.tar.gz"
    _make_tar_gz(tar_path, member_name="chunk_0.ndjson", body=b'{"a":1}\n{"a":2}')

    lines = list(iter_ndjson_lines(tar_path))

    assert lines == [b'{"a":1}', b'{"a":2}']


def test_rejects_line_exceeding_max_bytes(tmp_path: Path) -> None:
    tar_path = tmp_path / "chunk_0.tar.gz"
    _make_tar_gz(tar_path, member_name="chunk_0.ndjson", body=b"x" * 100 + b"\n")

    with pytest.raises(TarStreamError, match="exceeded"):
        list(iter_ndjson_lines(tar_path, max_line_bytes=10))


def test_rejects_empty_archive(tmp_path: Path) -> None:
    tar_path = tmp_path / "empty.tar.gz"
    with tarfile.open(tar_path, mode="w:gz"):
        pass

    with pytest.raises(TarStreamError, match="no members"):
        list(iter_ndjson_lines(tar_path))


def test_rejects_second_member(tmp_path: Path) -> None:
    tar_path = tmp_path / "chunk_0.tar.gz"
    with tarfile.open(tar_path, mode="w:gz") as archive:
        first = tarfile.TarInfo(name="chunk_0.ndjson")
        first.size = 8
        archive.addfile(first, io.BytesIO(b'{"a":1}\n'))
        second = tarfile.TarInfo(name="chunk_0_extra.ndjson")
        second.size = 8
        archive.addfile(second, io.BytesIO(b'{"a":2}\n'))

    with pytest.raises(TarStreamError, match="additional"):
        list(iter_ndjson_lines(tar_path))


def test_rejects_non_ndjson_member_name(tmp_path: Path) -> None:
    tar_path = tmp_path / "chunk_0.tar.gz"
    _make_tar_gz(tar_path, member_name="chunk_0.txt", body=b'{"a":1}\n')

    with pytest.raises(TarStreamError, match="unexpected name"):
        list(iter_ndjson_lines(tar_path))


def test_rejects_member_with_path_traversal_name(tmp_path: Path) -> None:
    tar_path = tmp_path / "chunk_0.tar.gz"
    _make_tar_gz(tar_path, member_name="../escape.ndjson", body=b'{"a":1}\n')

    with pytest.raises(TarStreamError, match="unexpected name"):
        list(iter_ndjson_lines(tar_path))


def test_rejects_symlink_member(tmp_path: Path) -> None:
    tar_path = tmp_path / "chunk_0.tar.gz"
    with tarfile.open(tar_path, mode="w:gz") as archive:
        info = tarfile.TarInfo(name="chunk_0.ndjson")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        archive.addfile(info)

    with pytest.raises(TarStreamError, match="regular file"):
        list(iter_ndjson_lines(tar_path))


def test_rejects_directory_member(tmp_path: Path) -> None:
    tar_path = tmp_path / "chunk_0.tar.gz"
    with tarfile.open(tar_path, mode="w:gz") as archive:
        info = tarfile.TarInfo(name="chunk_0.ndjson")
        info.type = tarfile.DIRTYPE
        archive.addfile(info)

    with pytest.raises(TarStreamError, match="regular file"):
        list(iter_ndjson_lines(tar_path))


def test_rejects_malformed_archive(tmp_path: Path) -> None:
    tar_path = tmp_path / "not-a-tar.tar.gz"
    tar_path.write_bytes(b"this is not a gzip stream at all")

    with pytest.raises(TarStreamError, match="cannot read tar archive"):
        list(iter_ndjson_lines(tar_path))


def test_non_positive_max_line_bytes_is_rejected(tmp_path: Path) -> None:
    tar_path = tmp_path / "chunk_0.tar.gz"
    _make_tar_gz(tar_path, member_name="chunk_0.ndjson", body=b'{"a":1}\n')

    with pytest.raises(TarStreamError, match="max_line_bytes"):
        list(iter_ndjson_lines(tar_path, max_line_bytes=0))
