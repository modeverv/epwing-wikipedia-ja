"""Resumable Snapshot chunk downloader: Range resume, atomic rename, bounded retry."""

from __future__ import annotations

import hashlib
import http.client
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from os import replace as os_replace
from pathlib import Path
from typing import Protocol, cast

DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 5
DEFAULT_READ_CHUNK_BYTES = 1 << 20
_URL_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")
_CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")
_REDIRECT_STATUSES = (301, 302, 303, 307, 308)


class ChunkDownloadError(RuntimeError):
    """Raised when a Snapshot chunk cannot be downloaded safely."""


class ChunkDownloadAuthError(ChunkDownloadError):
    """Raised when the chunk download is rejected as unauthorized/forbidden; never retried."""


@dataclass(frozen=True, slots=True)
class ChunkDownloadResult:
    """The verified outcome of one completed chunk download."""

    size_bytes: int
    sha256: str


class RangeResponse(Protocol):
    """The subset of a streaming HTTP response the downloader relies on."""

    status: int

    def getheader(self, name: str) -> str | None: ...

    def read(self, size: int) -> bytes: ...

    def close(self) -> None: ...

    def __enter__(self) -> RangeResponse: ...

    def __exit__(self, *exc_info: object) -> bool | None: ...


class ChunkTransport(Protocol):
    """Network operation required to stream one Range of a Snapshot chunk."""

    def fetch_range(
        self,
        access_token: str,
        *,
        snapshot_identifier: str,
        chunk_identifier: str,
        range_header: str,
        timeout_seconds: float,
    ) -> RangeResponse: ...


class ResumableChunkDownloader:
    """Download one Snapshot chunk to disk, resuming and retrying as needed."""

    def __init__(
        self,
        transport: ChunkTransport,
        *,
        timeout_seconds: float = DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        read_chunk_bytes: int = DEFAULT_READ_CHUNK_BYTES,
    ) -> None:
        if timeout_seconds <= 0:
            raise ChunkDownloadError("download timeout_seconds must be positive")
        if max_retries < 0:
            raise ChunkDownloadError("max_retries must not be negative")
        if read_chunk_bytes < 1:
            raise ChunkDownloadError("read_chunk_bytes must be positive")
        self._transport = transport
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._read_chunk_bytes = read_chunk_bytes

    def download(
        self,
        access_token: str,
        *,
        snapshot_identifier: str,
        chunk_identifier: str,
        destination: Path,
    ) -> ChunkDownloadResult:
        """Download one chunk to `destination`, resuming a `.partial` file if present."""
        _validate_not_symlink("destination", destination)
        partial_path = destination.with_name(destination.name + ".partial")
        _validate_not_symlink("partial download path", partial_path)

        attempts = 0
        total_size = -1
        while True:
            offset = partial_path.stat().st_size if partial_path.exists() else 0
            range_header = f"bytes={offset}-"
            try:
                total_size = self._stream_once(
                    access_token,
                    snapshot_identifier,
                    chunk_identifier,
                    range_header,
                    offset,
                    partial_path,
                )
                break
            except ChunkDownloadAuthError:
                raise
            except ChunkDownloadError:
                attempts += 1
                if attempts > self._max_retries:
                    raise
                continue

        final_size = partial_path.stat().st_size
        if final_size != total_size:
            raise ChunkDownloadError(
                f"chunk download incomplete: expected {total_size} bytes, got {final_size}"
            )
        sha256 = _sha256_file(partial_path)
        os_replace(partial_path, destination)
        return ChunkDownloadResult(size_bytes=final_size, sha256=sha256)

    def _stream_once(
        self,
        access_token: str,
        snapshot_identifier: str,
        chunk_identifier: str,
        range_header: str,
        offset: int,
        partial_path: Path,
    ) -> int:
        with self._transport.fetch_range(
            access_token,
            snapshot_identifier=snapshot_identifier,
            chunk_identifier=chunk_identifier,
            range_header=range_header,
            timeout_seconds=self._timeout_seconds,
        ) as response:
            if response.status not in (200, 206):
                raise ChunkDownloadError(f"unexpected chunk stream status: {response.status}")
            total_size = _parse_total_size(response, offset)
            try:
                with partial_path.open("ab") as file:
                    while True:
                        data = response.read(self._read_chunk_bytes)
                        if not data:
                            break
                        file.write(data)
            except OSError as error:
                raise ChunkDownloadError(f"chunk stream interrupted: {error}") from error
        return total_size


def _parse_total_size(response: RangeResponse, offset: int) -> int:
    if response.status == 206:
        content_range = response.getheader("Content-Range")
        if not content_range:
            raise ChunkDownloadError("206 response is missing a Content-Range header")
        match = _CONTENT_RANGE.fullmatch(content_range.strip())
        if not match:
            raise ChunkDownloadError(f"unparseable Content-Range header: {content_range!r}")
        start = int(match.group(1))
        if start != offset:
            raise ChunkDownloadError(
                f"server returned range starting at {start}, expected {offset}"
            )
        return int(match.group(3))
    if offset != 0:
        raise ChunkDownloadError("server returned full content (200) despite a resumed request")
    content_length = response.getheader("Content-Length")
    if content_length is None or not content_length.isdigit():
        raise ChunkDownloadError("200 response is missing a valid Content-Length header")
    return int(content_length)


def _validate_not_symlink(label: str, path: Path) -> None:
    if not path.is_absolute():
        raise ChunkDownloadError(f"{label} must be an absolute path: {path}")
    if path.is_symlink():
        raise ChunkDownloadError(f"{label} must not be a symlink: {path}")


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _require_url_segment(label: str, value: str) -> str:
    if not value or not _URL_SEGMENT.fullmatch(value):
        raise ChunkDownloadError(f"{label} must be a safe URL path segment: {value!r}")
    return value


class HttpChunkTransport:
    """Two-hop HTTPS transport: API redirect, then a bare Range GET to storage.

    The API responds to `GET /snapshots/{snapshot}/chunks/{chunk}/download` with an
    HTTP redirect to a short-lived, pre-signed storage URL. The `Authorization`
    header must not be forwarded to that URL, so the redirect is followed manually.
    """

    def __init__(
        self,
        api_base: str,
        *,
        redirect_opener: urllib.request.OpenerDirector | None = None,
        follow_opener: urllib.request.OpenerDirector | None = None,
    ) -> None:
        if not api_base.startswith("https://"):
            raise ChunkDownloadError("chunk download API base URL must use https://")
        self._api_base = api_base.rstrip("/")
        self._redirect_opener = redirect_opener or _build_no_redirect_opener()
        self._follow_opener = follow_opener or urllib.request.build_opener()

    def fetch_range(
        self,
        access_token: str,
        *,
        snapshot_identifier: str,
        chunk_identifier: str,
        range_header: str,
        timeout_seconds: float,
    ) -> RangeResponse:
        """Fetch one Range of a chunk, following the storage redirect without auth."""
        if timeout_seconds <= 0:
            raise ChunkDownloadError("download timeout_seconds must be positive")
        if not access_token:
            raise ChunkDownloadError("access_token must not be empty")
        _require_url_segment("snapshot_identifier", snapshot_identifier)
        _require_url_segment("chunk_identifier", chunk_identifier)
        url = f"{self._api_base}/snapshots/{snapshot_identifier}/chunks/{chunk_identifier}/download"
        request = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {access_token}", "Range": range_header},
            method="GET",
        )
        response = _open(self._redirect_opener, request, timeout_seconds, "chunk download")
        if response.status in (401, 403):
            code = response.status
            response.close()
            raise ChunkDownloadAuthError(f"chunk download rejected: HTTP {code}")
        if response.status in _REDIRECT_STATUSES:
            location = response.getheader("Location")
            response.close()
            if not location:
                raise ChunkDownloadError("chunk download redirect is missing a Location header")
            storage_request = urllib.request.Request(
                location, headers={"Range": range_header}, method="GET"
            )
            return _open(self._follow_opener, storage_request, timeout_seconds, "chunk storage")
        if response.status in (200, 206):
            return response
        code = response.status
        response.close()
        raise ChunkDownloadError(f"chunk download failed: unexpected HTTP {code}")


def _open(
    opener: urllib.request.OpenerDirector,
    request: urllib.request.Request,
    timeout_seconds: float,
    label: str,
) -> RangeResponse:
    try:
        return cast(RangeResponse, opener.open(request, timeout=timeout_seconds))
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise ChunkDownloadAuthError(f"{label} rejected: HTTP {error.code}") from error
        raise ChunkDownloadError(f"{label} request failed: HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise ChunkDownloadError(f"{label} request failed: {error.reason}") from error
    except TimeoutError as error:
        raise ChunkDownloadError(
            f"{label} request timed out after {timeout_seconds:g} seconds"
        ) from error


def _build_no_redirect_opener() -> urllib.request.OpenerDirector:
    class _NoRedirect(urllib.request.HTTPErrorProcessor):
        def http_response(
            self, request: urllib.request.Request, response: http.client.HTTPResponse
        ) -> http.client.HTTPResponse:
            return response

        https_response = http_response

    return urllib.request.build_opener(_NoRedirect)
