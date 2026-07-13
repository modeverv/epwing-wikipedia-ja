import hashlib
import urllib.request
from io import BytesIO
from pathlib import Path

import pytest

import wikiepwing.dump.downloader as downloader
from wikiepwing.dump.downloader import (
    DownloadError,
    checksum_url,
    dump_url,
    parse_sha1sums,
    parse_sha1sums_entry,
    register_local,
    sha1,
)


def test_dump_url_is_stable() -> None:
    assert dump_url("jawiki", "20260701").endswith("jawiki-20260701-pages-articles.xml.bz2")


def test_register_local_hashes_without_copying(tmp_path: Path) -> None:
    dump = tmp_path / "jawiki.xml.bz2"
    dump.write_bytes(b"fixture dump")
    manifest_path = tmp_path / "manifest.json"

    manifest = register_local(dump, "jawiki", "20260701", manifest_path)

    assert manifest.local_path == str(dump.resolve())
    assert manifest.checksum == sha1(dump)
    assert manifest_path.exists()


def test_parses_wikimedia_sha1sums() -> None:
    expected = "a" * 40
    assert parse_sha1sums(f"{expected}  jawiki.xml.bz2\n", "jawiki.xml.bz2") == expected


def test_rejects_missing_checksum() -> None:
    with pytest.raises(DownloadError, match="does not contain"):
        parse_sha1sums("a" * 40 + "  other.xml.bz2\n", "jawiki.xml.bz2")


def test_latest_checksum_selects_immutable_filename() -> None:
    checksum = "b" * 40
    assert parse_sha1sums_entry(
        f"{checksum}  jawiki-20260701-pages-articles.xml.bz2\n",
        "jawiki-latest-pages-articles.xml.bz2",
    ) == (checksum, "jawiki-20260701-pages-articles.xml.bz2")


def test_checksum_url_uses_dump_directory() -> None:
    url = "https://dumps.example/jawiki/20260701/jawiki-20260701-pages-articles.xml.bz2"
    assert checksum_url(url) == "https://dumps.example/jawiki/20260701/jawiki-20260701-sha1sums.txt"


class _Response(BytesIO):
    status = 206
    headers = {"Content-Length": "3"}

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def test_download_resumes_partial_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    destination = tmp_path / "dump.bz2"
    destination.with_suffix(".bz2.part").write_bytes(b"abc")
    expected = hashlib.sha1(b"abcdef").hexdigest()

    def fake_urlopen(request: urllib.request.Request, timeout: int) -> _Response:
        assert request.headers["Range"] == "bytes=3-"
        assert timeout == 60
        return _Response(b"def")

    monkeypatch.setattr(downloader.urllib.request, "urlopen", fake_urlopen)

    assert (
        downloader.download("https://example.test/dump.bz2", destination, expected) == destination
    )
    assert destination.read_bytes() == b"abcdef"
    assert not destination.with_suffix(".bz2.part").exists()
