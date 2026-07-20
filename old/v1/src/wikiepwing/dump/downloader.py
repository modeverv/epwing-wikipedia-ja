"""Resumable, checksum-verified Wikimedia dump acquisition."""

from __future__ import annotations

import fcntl
import hashlib
import json
import shutil
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path


class DownloadError(RuntimeError):
    """Raised for a dump that cannot safely be acquired or registered."""


USER_AGENT = "wikiepwing/0.1 (local Wikimedia dump builder)"


@dataclass(frozen=True, slots=True)
class DumpManifest:
    project: str
    dump_date: str
    source_url: str
    checksum_algorithm: str
    checksum: str
    local_path: str
    size_bytes: int


def dump_url(project: str, date: str, base_url: str = "https://dumps.wikimedia.org") -> str:
    """Return the pages-articles dump URL without resolving mutable metadata."""
    if not project.isalnum() or not project.endswith("wiki"):
        raise DownloadError("project must be an alphanumeric Wikimedia project ending in 'wiki'")
    if date != "latest" and (len(date) != 8 or not date.isdigit()):
        raise DownloadError("date must be 'latest' or YYYYMMDD")
    stem = f"{project}-{date}-pages-articles.xml.bz2"
    return f"{base_url.rstrip('/')}/{project}/{date}/{stem}"


def sha1(path: Path) -> str:
    """Compute a streaming SHA-1 digest."""
    digest = hashlib.sha1()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sha1sums_entry(contents: str, filename: str) -> tuple[str, str]:
    """Extract a SHA-1 and immutable filename from Wikimedia checksum metadata."""
    latest_suffix = filename.split("-latest-", 1)[-1] if "-latest-" in filename else None
    for line in contents.splitlines():
        fields = line.split()
        candidate_name = fields[-1].lstrip("*") if len(fields) >= 2 else ""
        matches_latest = latest_suffix is not None and candidate_name.endswith(latest_suffix)
        if candidate_name == filename or matches_latest:
            candidate = fields[0]
            if len(candidate) == 40 and all(char in "0123456789abcdefABCDEF" for char in candidate):
                return candidate.lower(), candidate_name
            raise DownloadError(f"invalid SHA-1 metadata for {filename}")
    raise DownloadError(f"checksum metadata does not contain {filename}")


def parse_sha1sums(contents: str, filename: str) -> str:
    """Extract a SHA-1 for one dump file from Wikimedia's sha1sums format."""
    return parse_sha1sums_entry(contents, filename)[0]


def checksum_url(url: str) -> str:
    """Return the Wikimedia checksum sidecar URL for a dump URL."""
    filename = Path(url).name
    project, date = filename.split("-", 2)[:2]
    return url.rsplit("/", 1)[0] + f"/{project}-{date}-sha1sums.txt"


def fetch_sha1sums_entry(url: str) -> tuple[str, str]:
    """Fetch a dump checksum and the immutable dump filename it names."""
    try:
        request = urllib.request.Request(checksum_url(url), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            contents = response.read().decode("utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as error:
        raise DownloadError(f"failed to fetch checksum metadata: {error}") from error
    return parse_sha1sums_entry(contents, Path(url).name)


def fetch_sha1(url: str) -> str:
    """Fetch and parse the sidecar checksum for one dump URL."""
    return fetch_sha1sums_entry(url)[0]


@contextmanager
def download_lock(path: Path) -> Iterator[None]:
    """Serialize processes targeting the same dump without stale lock files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _require_space(destination: Path, content_length: int | None) -> None:
    if content_length is None:
        return
    available = shutil.disk_usage(destination.parent).free
    if available < content_length:
        raise DownloadError(f"insufficient free disk space for {content_length} bytes")


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def register_local(path: Path, project: str, dump_date: str, manifest_path: Path) -> DumpManifest:
    """Hash an existing dump in place and write an atomic source manifest."""
    resolved = path.resolve()
    if not resolved.is_file():
        raise DownloadError(f"local dump is not a file: {resolved}")
    manifest = DumpManifest(
        project,
        dump_date,
        resolved.as_uri(),
        "sha1",
        sha1(resolved),
        str(resolved),
        resolved.stat().st_size,
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json(manifest_path, asdict(manifest))
    return manifest


def write_remote_manifest(
    path: Path, project: str, dump_date: str, source_url: str, manifest_path: Path
) -> DumpManifest:
    """Record a verified remote dump while retaining its immutable source URL."""
    resolved = path.resolve()
    manifest = DumpManifest(
        project,
        dump_date,
        source_url,
        "sha1",
        sha1(resolved),
        str(resolved),
        resolved.stat().st_size,
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json(manifest_path, asdict(manifest))
    return manifest


def download(url: str, destination: Path, expected_sha1: str) -> Path:
    """Resume a HTTP download into a `.part` file, then atomically promote it."""
    with download_lock(destination.with_suffix(destination.suffix + ".lock")):
        if destination.exists() and sha1(destination).lower() == expected_sha1.lower():
            return destination
        partial = destination.with_suffix(destination.suffix + ".part")
        offset = partial.stat().st_size if partial.exists() else 0
        headers = {"User-Agent": USER_AGENT}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        request = urllib.request.Request(url, headers=headers)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    length_header = response.headers.get("Content-Length")
                    _require_space(partial, (int(length_header) if length_header else None))
                    status = getattr(response, "status", 200)
                    mode = "ab" if offset and status == 206 else "wb"
                    with partial.open(mode) as target:
                        shutil.copyfileobj(response, target, length=1024 * 1024)
                break
            except OSError as error:
                if attempt == 2:
                    raise DownloadError(f"download failed after 3 attempts: {error}") from error
                time.sleep(2**attempt)
        actual = sha1(partial)
        if actual.lower() != expected_sha1.lower():
            raise DownloadError(f"checksum mismatch: expected {expected_sha1}, got {actual}")
        partial.replace(destination)
    return destination
