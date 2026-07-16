"""Secure media downloader (TASK-O004, ARCHITECTURE.md 15.4).

Covers 15.4's network-layer safety requirements for fetching a
`MediaReference.source_url`: HTTPS only, a host allowlist, a bounded
number of redirect hops (re-validating HTTPS/allowlist at every hop --
a redirect is exactly how an allowlisted URL could otherwise be used to
reach a disallowed host), a request timeout, and a `Content-Length` cap
enforced both from the response header (fail fast, before reading
anything) and while actually streaming the body (defense in depth
against a server that lies about its own `Content-Length`).

"実デコード後pixel上限" and "MIMEとmagic byte検証" need the bytes
actually decoded, so they're TASK-O005's job; "SVG sanitize" is
TASK-O006's. This module only gets the raw bytes home safely.

Real rendered HTML overwhelmingly uses protocol-relative `<img src>`
values (`//upload.wikimedia.org/...`, no explicit scheme) rather than
`https://...`; `download()` resolves those to `https://` before
validating/fetching (the sole scheme this project ever allows, so the
resolution is unambiguous), rather than rejecting a URL shape normal
browsers already treat as https on an https page.

Wikimedia's CDN (upload.wikimedia.org) enforces its User-Agent policy
(https://meta.wikimedia.org/wiki/User-Agent_policy) and returns a bare
403 -- not a helpful error body -- for requests using a generic library
default (e.g. `Python-urllib/3.x`). `_UrllibTransport` sends a
descriptive User-Agent identifying this project for that reason.
"""

from __future__ import annotations

import http.client
import urllib.error
import urllib.request
from dataclasses import dataclass
from importlib.metadata import version
from typing import Protocol, cast
from urllib.parse import urlsplit

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_REDIRECTS = 5
DEFAULT_MAX_CONTENT_LENGTH_BYTES = 20 * 1024 * 1024
_REDIRECT_STATUSES = (301, 302, 303, 307, 308)
_READ_CHUNK_BYTES = 1 << 16
_USER_AGENT = (
    f"wikiepwing/{version('wikiepwing')} "
    "(https://github.com/modeverv/epwing-wikipedia-ja; batch dictionary build)"
)


class MediaDownloadError(RuntimeError):
    """Raised when a media reference cannot be downloaded safely."""


@dataclass(frozen=True, slots=True)
class MediaDownloadResult:
    """The verified outcome of one completed media download."""

    content: bytes
    content_type: str | None


class MediaResponse(Protocol):
    """The subset of an HTTP response the downloader relies on."""

    status: int

    def getheader(self, name: str) -> str | None: ...

    def read(self, size: int) -> bytes: ...

    def close(self) -> None: ...


class MediaTransport(Protocol):
    """Network operation required to fetch one URL."""

    def open(self, url: str, *, timeout_seconds: float) -> MediaResponse: ...


class SecureMediaDownloader:
    """Download a media URL, enforcing 15.4's HTTPS/allowlist/redirect/size limits."""

    def __init__(
        self,
        *,
        allowed_hosts: frozenset[str],
        transport: MediaTransport | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        max_content_length_bytes: int = DEFAULT_MAX_CONTENT_LENGTH_BYTES,
    ) -> None:
        if timeout_seconds <= 0:
            raise MediaDownloadError("timeout_seconds must be positive")
        if max_redirects < 0:
            raise MediaDownloadError("max_redirects must not be negative")
        if max_content_length_bytes < 1:
            raise MediaDownloadError("max_content_length_bytes must be positive")
        self._allowed_hosts = allowed_hosts
        self._transport = transport or _UrllibTransport()
        self._timeout_seconds = timeout_seconds
        self._max_redirects = max_redirects
        self._max_content_length_bytes = max_content_length_bytes

    def download(self, url: str) -> MediaDownloadResult:
        """Fetch `url`, following redirects safely, and return its validated bytes."""
        current_url = url
        for _ in range(self._max_redirects + 1):
            current_url = _resolve_protocol_relative(current_url)
            self._validate_url(current_url)
            response = self._transport.open(current_url, timeout_seconds=self._timeout_seconds)
            try:
                if response.status in _REDIRECT_STATUSES:
                    location = response.getheader("Location")
                    if not location:
                        raise MediaDownloadError("redirect response is missing a Location header")
                    current_url = location
                    continue
                if response.status != 200:
                    raise MediaDownloadError(f"unexpected HTTP status: {response.status}")
                return MediaDownloadResult(
                    content=self._read_body(response),
                    content_type=response.getheader("Content-Type"),
                )
            finally:
                response.close()
        raise MediaDownloadError(f"too many redirects (max {self._max_redirects})")

    def _validate_url(self, url: str) -> None:
        parts = urlsplit(url)
        if parts.scheme != "https":
            raise MediaDownloadError(f"media URL must use https://: {url!r}")
        if parts.hostname not in self._allowed_hosts:
            raise MediaDownloadError(f"host not in allowlist: {parts.hostname!r}")

    def _read_body(self, response: MediaResponse) -> bytes:
        content_length = response.getheader("Content-Length")
        if content_length is not None and content_length.isdigit():
            if int(content_length) > self._max_content_length_bytes:
                raise MediaDownloadError(
                    f"Content-Length {content_length} exceeds the "
                    f"{self._max_content_length_bytes}-byte limit"
                )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(_READ_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > self._max_content_length_bytes:
                raise MediaDownloadError(
                    f"downloaded body exceeds the {self._max_content_length_bytes}-byte limit"
                )
            chunks.append(chunk)
        return b"".join(chunks)


def _resolve_protocol_relative(url: str) -> str:
    """Resolve a `//host/path` URL to `https://host/path`; leave every other URL as-is."""
    return f"https:{url}" if url.startswith("//") else url


class _UrllibTransport:
    """Default `MediaTransport`: a single GET per hop, redirects never auto-followed."""

    def __init__(self) -> None:
        self._opener = _build_no_redirect_opener()

    def open(self, url: str, *, timeout_seconds: float) -> MediaResponse:
        request = urllib.request.Request(url, method="GET", headers={"User-Agent": _USER_AGENT})
        try:
            return cast(MediaResponse, self._opener.open(request, timeout=timeout_seconds))
        except urllib.error.HTTPError as error:
            raise MediaDownloadError(f"media download failed: HTTP {error.code}") from error
        except urllib.error.URLError as error:
            raise MediaDownloadError(f"media download failed: {error.reason}") from error
        except TimeoutError as error:
            raise MediaDownloadError(
                f"media download timed out after {timeout_seconds:g} seconds"
            ) from error


def _build_no_redirect_opener() -> urllib.request.OpenerDirector:
    class _NoRedirect(urllib.request.HTTPErrorProcessor):
        def http_response(
            self, request: urllib.request.Request, response: http.client.HTTPResponse
        ) -> http.client.HTTPResponse:
            return response

        https_response = http_response

    return urllib.request.build_opener(_NoRedirect)
