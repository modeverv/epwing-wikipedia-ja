from __future__ import annotations

import urllib.request
from dataclasses import dataclass, field

import pytest

from wikiepwing.media.downloader import (
    MediaDownloadError,
    SecureMediaDownloader,
    _UrllibTransport,
)


@dataclass
class _FakeResponse:
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    _offset: int = 0
    closed: bool = False

    def getheader(self, name: str) -> str | None:
        return self.headers.get(name)

    def read(self, size: int) -> bytes:
        chunk = self.body[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


class _FakeTransport:
    def __init__(self, responses_by_url: dict[str, _FakeResponse]) -> None:
        self._responses_by_url = responses_by_url
        self.opened_urls: list[str] = []

    def open(self, url: str, *, timeout_seconds: float) -> _FakeResponse:
        self.opened_urls.append(url)
        if url not in self._responses_by_url:
            raise AssertionError(f"unexpected URL requested: {url}")
        return self._responses_by_url[url]


class _SequentialTransport:
    """Returns each queued response in order, regardless of URL (for retry tests)."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.opened_urls: list[str] = []

    def open(self, url: str, *, timeout_seconds: float) -> _FakeResponse:
        self.opened_urls.append(url)
        if not self._responses:
            raise AssertionError(f"no more queued responses, but {url} was requested")
        return self._responses.pop(0)


def _downloader(transport: object, **overrides: object) -> SecureMediaDownloader:
    defaults: dict[str, object] = {
        "allowed_hosts": frozenset({"example.org"}),
        "transport": transport,
    }
    defaults.update(overrides)
    return SecureMediaDownloader(**defaults)  # type: ignore[arg-type]


def test_rejects_non_https_url() -> None:
    downloader = _downloader(_FakeTransport({}))

    with pytest.raises(MediaDownloadError, match="https"):
        downloader.download("http://example.org/a.png")


def test_resolves_protocol_relative_url_to_https() -> None:
    # Real rendered HTML overwhelmingly uses `<img src="//host/path">` (no
    # scheme) rather than a full https:// URL.
    resolved = "https://example.org/a.png"
    transport = _FakeTransport(
        {resolved: _FakeResponse(status=200, headers={"Content-Type": "image/png"}, body=b"x")}
    )
    downloader = _downloader(transport)

    result = downloader.download("//example.org/a.png")

    assert result.content == b"x"
    assert transport.opened_urls == [resolved]


def test_rejects_host_not_in_allowlist() -> None:
    downloader = _downloader(_FakeTransport({}))

    with pytest.raises(MediaDownloadError, match="allowlist"):
        downloader.download("https://evil.example/a.png")


def test_successful_download_returns_content_and_type() -> None:
    url = "https://example.org/a.png"
    transport = _FakeTransport(
        {url: _FakeResponse(status=200, headers={"Content-Type": "image/png"}, body=b"pngbytes")}
    )
    downloader = _downloader(transport)

    result = downloader.download(url)

    assert result.content == b"pngbytes"
    assert result.content_type == "image/png"


def test_follows_redirect_and_revalidates_each_hop() -> None:
    first = "https://example.org/a.png"
    second = "https://example.org/b.png"
    transport = _FakeTransport(
        {
            first: _FakeResponse(status=302, headers={"Location": second}),
            second: _FakeResponse(status=200, body=b"final"),
        }
    )
    downloader = _downloader(transport)

    result = downloader.download(first)

    assert result.content == b"final"
    assert transport.opened_urls == [first, second]


def test_redirect_to_non_allowlisted_host_is_rejected() -> None:
    first = "https://example.org/a.png"
    transport = _FakeTransport(
        {first: _FakeResponse(status=302, headers={"Location": "https://evil.example/a.png"})}
    )
    downloader = _downloader(transport)

    with pytest.raises(MediaDownloadError, match="allowlist"):
        downloader.download(first)


def test_redirect_to_non_https_is_rejected() -> None:
    first = "https://example.org/a.png"
    transport = _FakeTransport(
        {first: _FakeResponse(status=302, headers={"Location": "http://example.org/a.png"})}
    )
    downloader = _downloader(transport)

    with pytest.raises(MediaDownloadError, match="https"):
        downloader.download(first)


def test_too_many_redirects_raises() -> None:
    urls = [f"https://example.org/{i}.png" for i in range(4)]
    responses = {
        urls[i]: _FakeResponse(status=302, headers={"Location": urls[i + 1]}) for i in range(3)
    }
    responses[urls[3]] = _FakeResponse(
        status=302, headers={"Location": "https://example.org/4.png"}
    )
    transport = _FakeTransport(responses)
    downloader = _downloader(transport, max_redirects=2)

    with pytest.raises(MediaDownloadError, match="too many redirects"):
        downloader.download(urls[0])


def test_redirect_missing_location_header_raises() -> None:
    url = "https://example.org/a.png"
    transport = _FakeTransport({url: _FakeResponse(status=302, headers={})})
    downloader = _downloader(transport)

    with pytest.raises(MediaDownloadError, match="Location"):
        downloader.download(url)


def test_unexpected_status_raises() -> None:
    url = "https://example.org/a.png"
    transport = _FakeTransport({url: _FakeResponse(status=500)})
    downloader = _downloader(transport)

    with pytest.raises(MediaDownloadError, match="500"):
        downloader.download(url)


def test_content_length_header_over_limit_is_rejected_before_reading() -> None:
    url = "https://example.org/a.png"
    response = _FakeResponse(status=200, headers={"Content-Length": "1000"}, body=b"x" * 1000)
    transport = _FakeTransport({url: response})
    downloader = _downloader(transport, max_content_length_bytes=10)

    with pytest.raises(MediaDownloadError, match="Content-Length"):
        downloader.download(url)

    assert response._offset == 0


def test_body_exceeding_limit_without_content_length_header_is_rejected() -> None:
    url = "https://example.org/a.png"
    response = _FakeResponse(status=200, body=b"x" * 1000)
    transport = _FakeTransport({url: response})
    downloader = _downloader(transport, max_content_length_bytes=10)

    with pytest.raises(MediaDownloadError, match="exceeds"):
        downloader.download(url)


def test_response_is_always_closed_on_success() -> None:
    url = "https://example.org/a.png"
    response = _FakeResponse(status=200, body=b"ok")
    transport = _FakeTransport({url: response})
    downloader = _downloader(transport)

    downloader.download(url)

    assert response.closed is True


def test_response_is_closed_even_when_over_limit() -> None:
    url = "https://example.org/a.png"
    response = _FakeResponse(status=200, body=b"x" * 1000)
    transport = _FakeTransport({url: response})
    downloader = _downloader(transport, max_content_length_bytes=10)

    with pytest.raises(MediaDownloadError):
        downloader.download(url)

    assert response.closed is True


def test_rejects_non_positive_timeout() -> None:
    with pytest.raises(MediaDownloadError, match="timeout_seconds"):
        _downloader(_FakeTransport({}), timeout_seconds=0)


def test_rejects_negative_max_redirects() -> None:
    with pytest.raises(MediaDownloadError, match="max_redirects"):
        _downloader(_FakeTransport({}), max_redirects=-1)


def test_rejects_non_positive_max_content_length() -> None:
    with pytest.raises(MediaDownloadError, match="max_content_length_bytes"):
        _downloader(_FakeTransport({}), max_content_length_bytes=0)


def test_rejects_negative_max_rate_limit_retries() -> None:
    with pytest.raises(MediaDownloadError, match="max_rate_limit_retries"):
        _downloader(_FakeTransport({}), max_rate_limit_retries=-1)


def test_retries_429_and_succeeds_within_budget() -> None:
    transport = _SequentialTransport(
        [
            _FakeResponse(status=429, headers={"Retry-After": "0"}),
            _FakeResponse(status=429, headers={"Retry-After": "0"}),
            _FakeResponse(status=200, headers={"Content-Type": "image/png"}, body=b"ok"),
        ]
    )
    sleeps: list[float] = []
    downloader = _downloader(transport, max_rate_limit_retries=5, sleep=sleeps.append)

    result = downloader.download("https://example.org/a.png")

    assert result.content == b"ok"
    assert sleeps == [0.0, 0.0]


def test_429_retry_uses_retry_after_header_when_present() -> None:
    transport = _SequentialTransport(
        [
            _FakeResponse(status=429, headers={"Retry-After": "7"}),
            _FakeResponse(status=200, body=b"ok"),
        ]
    )
    sleeps: list[float] = []
    downloader = _downloader(transport, sleep=sleeps.append)

    downloader.download("https://example.org/a.png")

    assert sleeps == [7.0]


def test_429_retry_falls_back_to_exponential_backoff_without_retry_after() -> None:
    transport = _SequentialTransport(
        [
            _FakeResponse(status=429),
            _FakeResponse(status=429),
            _FakeResponse(status=200, body=b"ok"),
        ]
    )
    sleeps: list[float] = []
    downloader = _downloader(transport, sleep=sleeps.append)

    downloader.download("https://example.org/a.png")

    assert sleeps == [2.0, 4.0]


def test_gives_up_after_exhausting_rate_limit_retries() -> None:
    transport = _SequentialTransport(
        [
            _FakeResponse(status=429, headers={"Retry-After": "0"}),
            _FakeResponse(status=429, headers={"Retry-After": "0"}),
        ]
    )
    downloader = _downloader(transport, max_rate_limit_retries=1, sleep=lambda _seconds: None)

    with pytest.raises(MediaDownloadError, match="rate-limited"):
        downloader.download("https://example.org/a.png")


def test_urllib_transport_sends_a_descriptive_user_agent() -> None:
    # Wikimedia's CDN returns a bare 403 for a generic library User-Agent
    # (e.g. "Python-urllib/3.x"); the real transport must identify itself.
    transport = _UrllibTransport()
    captured: dict[str, urllib.request.Request] = {}

    class _FakeOpener:
        def open(self, request: urllib.request.Request, *, timeout: float) -> _FakeResponse:
            captured["request"] = request
            return _FakeResponse(status=200, body=b"x")

    transport._opener = _FakeOpener()  # type: ignore[assignment]

    transport.open("https://example.org/a.png", timeout_seconds=1.0)

    user_agent = captured["request"].get_header("User-agent")
    assert user_agent is not None
    assert user_agent.startswith("wikiepwing/")
