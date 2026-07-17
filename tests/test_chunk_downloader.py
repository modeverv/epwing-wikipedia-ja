from __future__ import annotations

import hashlib
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from wikiepwing.source.downloader import (
    ChunkDownloadAuthError,
    ChunkDownloadError,
    ChunkDownloadProgress,
    HttpChunkTransport,
    ResumableChunkDownloader,
)


class _FakeResponse:
    def __init__(
        self,
        *,
        status: int,
        headers: dict[str, str] | None = None,
        chunks: list[bytes] | None = None,
        fail_after: int | None = None,
    ) -> None:
        self.status = status
        self._headers = headers or {}
        self._chunks = list(chunks or [])
        self._reads = 0
        self._fail_after = fail_after
        self.closed = False

    def getheader(self, name: str) -> str | None:
        return self._headers.get(name)

    def read(self, size: int) -> bytes:
        if self._fail_after is not None and self._reads >= self._fail_after:
            raise OSError("simulated connection drop")
        self._reads += 1
        if not self._chunks:
            return b""
        return self._chunks.pop(0)

    def close(self) -> None:
        self.closed = True

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None


class _FakeTransport:
    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def fetch_range(
        self,
        access_token: str,
        *,
        snapshot_identifier: str,
        chunk_identifier: str,
        range_header: str,
        timeout_seconds: float,
    ) -> Any:
        self.calls.append(
            {
                "access_token": access_token,
                "snapshot_identifier": snapshot_identifier,
                "chunk_identifier": chunk_identifier,
                "range_header": range_header,
                "timeout_seconds": timeout_seconds,
            }
        )
        next_response = self._responses.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return next_response


def test_downloads_full_content_in_one_attempt(tmp_path: Path) -> None:
    content = b"HELLOWORLD"
    response = _FakeResponse(
        status=200,
        headers={"Content-Length": str(len(content))},
        chunks=[content],
    )
    transport = _FakeTransport([response])
    downloader = ResumableChunkDownloader(transport)
    destination = tmp_path / "chunk_0.tar.gz"

    result = downloader.download(
        "token",
        snapshot_identifier="jawiki_namespace_0",
        chunk_identifier="jawiki_namespace_0_chunk_0",
        destination=destination,
    )

    assert destination.read_bytes() == content
    assert not destination.with_name(destination.name + ".partial").exists()
    assert result.size_bytes == len(content)
    assert result.sha256 == hashlib.sha256(content).hexdigest()
    assert transport.calls == [
        {
            "access_token": "token",
            "snapshot_identifier": "jawiki_namespace_0",
            "chunk_identifier": "jawiki_namespace_0_chunk_0",
            "range_header": "bytes=0-",
            "timeout_seconds": 60.0,
        }
    ]


def test_on_progress_reports_periodic_byte_counts_and_a_final_event(tmp_path: Path) -> None:
    content = b"HELLOWORLD"
    response = _FakeResponse(
        status=200,
        headers={"Content-Length": str(len(content))},
        # Delivered in small pieces so progress fires more than once even
        # though the whole chunk is well under one progress_interval_bytes.
        chunks=[b"HELLO", b"WOR", b"LD"],
    )
    transport = _FakeTransport([response])
    downloader = ResumableChunkDownloader(transport, progress_interval_bytes=5)
    destination = tmp_path / "chunk_0.tar.gz"
    events: list[ChunkDownloadProgress] = []

    downloader.download(
        "token",
        snapshot_identifier="jawiki_namespace_0",
        chunk_identifier="jawiki_namespace_0_chunk_0",
        destination=destination,
        on_progress=events.append,
    )

    assert [event.bytes_downloaded for event in events] == [5, 10]
    assert all(event.total_bytes == len(content) for event in events)


def test_on_progress_reports_a_final_event_even_below_the_interval(tmp_path: Path) -> None:
    content = b"HI"
    response = _FakeResponse(
        status=200, headers={"Content-Length": str(len(content))}, chunks=[content]
    )
    transport = _FakeTransport([response])
    downloader = ResumableChunkDownloader(transport, progress_interval_bytes=1 << 20)
    destination = tmp_path / "chunk_0.tar.gz"
    events: list[ChunkDownloadProgress] = []

    downloader.download(
        "token",
        snapshot_identifier="jawiki_namespace_0",
        chunk_identifier="jawiki_namespace_0_chunk_0",
        destination=destination,
        on_progress=events.append,
    )

    assert [event.bytes_downloaded for event in events] == [2]


def test_resumes_from_existing_partial_file(tmp_path: Path) -> None:
    destination = tmp_path / "chunk_0.tar.gz"
    partial = destination.with_name(destination.name + ".partial")
    partial.write_bytes(b"ABCD")

    response = _FakeResponse(
        status=206,
        headers={"Content-Range": "bytes 4-9/10"},
        chunks=[b"EFGHIJ"],
    )
    transport = _FakeTransport([response])
    downloader = ResumableChunkDownloader(transport)

    result = downloader.download(
        "token",
        snapshot_identifier="jawiki_namespace_0",
        chunk_identifier="jawiki_namespace_0_chunk_0",
        destination=destination,
    )

    assert destination.read_bytes() == b"ABCDEFGHIJ"
    assert result.size_bytes == 10
    assert transport.calls[0]["range_header"] == "bytes=4-"


def test_retries_after_interrupted_stream_and_succeeds(tmp_path: Path) -> None:
    destination = tmp_path / "chunk_0.tar.gz"
    first = _FakeResponse(
        status=200,
        headers={"Content-Length": "10"},
        chunks=[b"HELL"],
        fail_after=1,
    )
    second = _FakeResponse(
        status=206,
        headers={"Content-Range": "bytes 4-9/10"},
        chunks=[b"OWORLD"],
    )
    transport = _FakeTransport([first, second])
    downloader = ResumableChunkDownloader(transport, max_retries=3)

    result = downloader.download(
        "token",
        snapshot_identifier="jawiki_namespace_0",
        chunk_identifier="jawiki_namespace_0_chunk_0",
        destination=destination,
    )

    assert destination.read_bytes() == b"HELLOWORLD"
    assert result.size_bytes == 10
    assert len(transport.calls) == 2
    assert transport.calls[1]["range_header"] == "bytes=4-"


def test_exceeding_max_retries_raises(tmp_path: Path) -> None:
    destination = tmp_path / "chunk_0.tar.gz"
    failing = [
        _FakeResponse(status=200, headers={"Content-Length": "10"}, chunks=[], fail_after=0)
        for _ in range(3)
    ]
    transport = _FakeTransport(failing)
    downloader = ResumableChunkDownloader(transport, max_retries=2)

    with pytest.raises(ChunkDownloadError, match="interrupted"):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=destination,
        )

    assert len(transport.calls) == 3


def test_auth_error_is_not_retried(tmp_path: Path) -> None:
    transport = _FakeTransport([ChunkDownloadAuthError("rejected: HTTP 401")])
    downloader = ResumableChunkDownloader(transport, max_retries=5)

    with pytest.raises(ChunkDownloadAuthError):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=tmp_path / "chunk_0.tar.gz",
        )

    assert len(transport.calls) == 1


def test_unexpected_status_is_rejected(tmp_path: Path) -> None:
    transport = _FakeTransport([_FakeResponse(status=500)])
    downloader = ResumableChunkDownloader(transport, max_retries=0)

    with pytest.raises(ChunkDownloadError, match="unexpected chunk stream status"):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=tmp_path / "chunk_0.tar.gz",
        )


def test_missing_content_range_on_206_is_rejected(tmp_path: Path) -> None:
    destination = tmp_path / "chunk_0.tar.gz"
    destination.with_name(destination.name + ".partial").write_bytes(b"AB")
    transport = _FakeTransport([_FakeResponse(status=206, chunks=[b"CD"])])
    downloader = ResumableChunkDownloader(transport, max_retries=0)

    with pytest.raises(ChunkDownloadError, match="Content-Range"):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=destination,
        )


def test_content_range_start_mismatch_is_rejected(tmp_path: Path) -> None:
    destination = tmp_path / "chunk_0.tar.gz"
    destination.with_name(destination.name + ".partial").write_bytes(b"AB")
    transport = _FakeTransport(
        [_FakeResponse(status=206, headers={"Content-Range": "bytes 0-9/10"}, chunks=[b"X"])]
    )
    downloader = ResumableChunkDownloader(transport, max_retries=0)

    with pytest.raises(ChunkDownloadError, match="expected 2"):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=destination,
        )


def test_full_content_returned_despite_resume_is_rejected(tmp_path: Path) -> None:
    destination = tmp_path / "chunk_0.tar.gz"
    destination.with_name(destination.name + ".partial").write_bytes(b"AB")
    transport = _FakeTransport(
        [_FakeResponse(status=200, headers={"Content-Length": "10"}, chunks=[b"X"])]
    )
    downloader = ResumableChunkDownloader(transport, max_retries=0)

    with pytest.raises(ChunkDownloadError, match="despite a resumed request"):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=destination,
        )


def test_missing_content_length_on_200_is_rejected(tmp_path: Path) -> None:
    transport = _FakeTransport([_FakeResponse(status=200, chunks=[b"X"])])
    downloader = ResumableChunkDownloader(transport, max_retries=0)

    with pytest.raises(ChunkDownloadError, match="Content-Length"):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=tmp_path / "chunk_0.tar.gz",
        )


def test_destination_must_be_absolute() -> None:
    downloader = ResumableChunkDownloader(_FakeTransport([]))

    with pytest.raises(ChunkDownloadError, match="absolute"):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=Path("relative/chunk_0.tar.gz"),
        )


def test_destination_must_not_be_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.tar.gz"
    real.write_bytes(b"x")
    link = tmp_path / "chunk_0.tar.gz"
    link.symlink_to(real)
    downloader = ResumableChunkDownloader(_FakeTransport([]))

    with pytest.raises(ChunkDownloadError, match="symlink"):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=link,
        )


def test_partial_path_must_not_be_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.partial"
    real.write_bytes(b"x")
    destination = tmp_path / "chunk_0.tar.gz"
    (tmp_path / "chunk_0.tar.gz.partial").symlink_to(real)
    downloader = ResumableChunkDownloader(_FakeTransport([]))

    with pytest.raises(ChunkDownloadError, match="symlink"):
        downloader.download(
            "token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            destination=destination,
        )


def test_non_positive_timeout_is_rejected() -> None:
    with pytest.raises(ChunkDownloadError):
        ResumableChunkDownloader(_FakeTransport([]), timeout_seconds=0)


def test_negative_max_retries_is_rejected() -> None:
    with pytest.raises(ChunkDownloadError):
        ResumableChunkDownloader(_FakeTransport([]), max_retries=-1)


def test_non_positive_read_chunk_bytes_is_rejected() -> None:
    with pytest.raises(ChunkDownloadError):
        ResumableChunkDownloader(_FakeTransport([]), read_chunk_bytes=0)


def test_non_positive_progress_interval_bytes_is_rejected() -> None:
    with pytest.raises(ChunkDownloadError):
        ResumableChunkDownloader(_FakeTransport([]), progress_interval_bytes=0)


# --- HttpChunkTransport: real two-hop redirect-then-storage dance ---


class _FakeOpener:
    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.requests: list[Any] = []

    def open(self, request: Any, timeout: float) -> Any:
        self.requests.append(request)
        assert timeout > 0
        next_response = self._responses.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return next_response


def test_http_transport_follows_redirect_without_forwarding_authorization() -> None:
    redirect_response = _FakeResponse(
        status=307,
        headers={"Location": "https://storage.example/chunks/x?X-Amz-Signature=abc"},
    )
    storage_response = _FakeResponse(
        status=206,
        headers={"Content-Range": "bytes 0-9/10"},
        chunks=[b"0123456789"],
    )
    redirect_opener = _FakeOpener([redirect_response])
    follow_opener = _FakeOpener([storage_response])
    transport = HttpChunkTransport(
        "https://api.enterprise.wikimedia.com/v2",
        redirect_opener=redirect_opener,
        follow_opener=follow_opener,
    )

    with transport.fetch_range(
        "secret-token",
        snapshot_identifier="jawiki_namespace_0",
        chunk_identifier="jawiki_namespace_0_chunk_0",
        range_header="bytes=0-",
        timeout_seconds=10.0,
    ) as response:
        assert response.status == 206
        assert response.read(1024) == b"0123456789"

    first_request = redirect_opener.requests[0]
    assert first_request.get_header("Authorization") == "Bearer secret-token"
    assert first_request.get_header("Range") == "bytes=0-"
    assert (
        first_request.full_url
        == "https://api.enterprise.wikimedia.com/v2/snapshots/jawiki_namespace_0"
        "/chunks/jawiki_namespace_0_chunk_0/download"
    )

    second_request = follow_opener.requests[0]
    assert second_request.get_header("Authorization") is None
    assert second_request.get_header("Range") == "bytes=0-"
    assert second_request.full_url == "https://storage.example/chunks/x?X-Amz-Signature=abc"


def test_http_transport_returns_direct_response_without_redirect() -> None:
    response = _FakeResponse(status=200, headers={"Content-Length": "3"}, chunks=[b"abc"])
    redirect_opener = _FakeOpener([response])
    transport = HttpChunkTransport(
        "https://api.enterprise.wikimedia.com/v2",
        redirect_opener=redirect_opener,
        follow_opener=_FakeOpener([]),
    )

    with transport.fetch_range(
        "secret-token",
        snapshot_identifier="jawiki_namespace_0",
        chunk_identifier="jawiki_namespace_0_chunk_0",
        range_header="bytes=0-",
        timeout_seconds=10.0,
    ) as returned:
        assert returned.status == 200


def test_http_transport_401_raises_auth_error_without_retry() -> None:
    redirect_opener = _FakeOpener([_FakeResponse(status=401)])
    transport = HttpChunkTransport(
        "https://api.enterprise.wikimedia.com/v2",
        redirect_opener=redirect_opener,
        follow_opener=_FakeOpener([]),
    )

    with pytest.raises(ChunkDownloadAuthError):
        transport.fetch_range(
            "secret-token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            range_header="bytes=0-",
            timeout_seconds=10.0,
        )


def test_http_transport_redirect_missing_location_is_rejected() -> None:
    redirect_opener = _FakeOpener([_FakeResponse(status=307, headers={})])
    transport = HttpChunkTransport(
        "https://api.enterprise.wikimedia.com/v2",
        redirect_opener=redirect_opener,
        follow_opener=_FakeOpener([]),
    )

    with pytest.raises(ChunkDownloadError, match="Location"):
        transport.fetch_range(
            "secret-token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            range_header="bytes=0-",
            timeout_seconds=10.0,
        )


def test_http_transport_requires_https() -> None:
    with pytest.raises(ChunkDownloadError):
        HttpChunkTransport("http://api.enterprise.wikimedia.com/v2")


def test_http_transport_requires_access_token() -> None:
    transport = HttpChunkTransport(
        "https://api.enterprise.wikimedia.com/v2",
        redirect_opener=_FakeOpener([]),
        follow_opener=_FakeOpener([]),
    )

    with pytest.raises(ChunkDownloadError, match="must not be empty"):
        transport.fetch_range(
            "",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            range_header="bytes=0-",
            timeout_seconds=10.0,
        )


def test_http_transport_rejects_unsafe_url_segment() -> None:
    transport = HttpChunkTransport(
        "https://api.enterprise.wikimedia.com/v2",
        redirect_opener=_FakeOpener([]),
        follow_opener=_FakeOpener([]),
    )

    with pytest.raises(ChunkDownloadError, match="URL path segment"):
        transport.fetch_range(
            "secret-token",
            snapshot_identifier="../etc",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            range_header="bytes=0-",
            timeout_seconds=10.0,
        )


def test_http_transport_timeout_raises() -> None:
    redirect_opener = _FakeOpener([TimeoutError("timed out")])
    transport = HttpChunkTransport(
        "https://api.enterprise.wikimedia.com/v2",
        redirect_opener=redirect_opener,
        follow_opener=_FakeOpener([]),
    )

    with pytest.raises(ChunkDownloadError, match="timed out"):
        transport.fetch_range(
            "secret-token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            range_header="bytes=0-",
            timeout_seconds=1.0,
        )


def test_http_transport_5xx_raises() -> None:
    def make_error() -> urllib.error.HTTPError:
        return urllib.error.HTTPError("https://example/x", 503, "unavailable", None, None)

    redirect_opener = _FakeOpener([make_error()])
    transport = HttpChunkTransport(
        "https://api.enterprise.wikimedia.com/v2",
        redirect_opener=redirect_opener,
        follow_opener=_FakeOpener([]),
    )

    with pytest.raises(ChunkDownloadError, match="503"):
        transport.fetch_range(
            "secret-token",
            snapshot_identifier="jawiki_namespace_0",
            chunk_identifier="jawiki_namespace_0_chunk_0",
            range_header="bytes=0-",
            timeout_seconds=1.0,
        )
