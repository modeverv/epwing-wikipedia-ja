"""Stream NDJSON lines out of a chunk's tar.gz archive without full extraction."""

from __future__ import annotations

import re
import tarfile
from collections.abc import Iterator
from pathlib import Path
from typing import IO

DEFAULT_MAX_LINE_BYTES = 8 * 1024 * 1024
_NDJSON_MEMBER_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.ndjson$")


class TarStreamError(RuntimeError):
    """Raised when a chunk archive cannot be streamed safely."""


def iter_ndjson_lines(
    tar_path: Path, *, max_line_bytes: int = DEFAULT_MAX_LINE_BYTES
) -> Iterator[bytes]:
    """Yield each NDJSON line from `tar_path`'s single member, without extracting to disk.

    Reads the archive in pure streaming mode (no seeking, no full extraction). The
    trailing "no additional member" check only completes once the caller has fully
    consumed this generator, since a streaming tar reader cannot look ahead without
    first passing through (or explicitly skipping) the current member's data.
    """
    if max_line_bytes < 1:
        raise TarStreamError("max_line_bytes must be positive")
    try:
        with tarfile.open(tar_path, mode="r|gz") as archive:
            member = archive.next()
            if member is None:
                raise TarStreamError("archive contained no members")
            _validate_member(member)
            stream = archive.extractfile(member)
            if stream is None:
                raise TarStreamError(f"cannot read tar member: {member.name}")
            yield from _iter_lines(stream, member.name, max_line_bytes)
            extra = archive.next()
            if extra is not None:
                raise TarStreamError(
                    f"expected exactly one archive member, found an additional one: {extra.name}"
                )
    except tarfile.TarError as error:
        raise TarStreamError(f"cannot read tar archive {tar_path}: {error}") from error


def _validate_member(member: tarfile.TarInfo) -> None:
    if not member.isfile():
        raise TarStreamError(
            f"archive member must be a regular file: {member.name} (type {member.type!r})"
        )
    if not _NDJSON_MEMBER_NAME.fullmatch(member.name):
        raise TarStreamError(f"archive member has an unexpected name: {member.name}")


def _iter_lines(stream: IO[bytes], member_name: str, max_line_bytes: int) -> Iterator[bytes]:
    while True:
        line = stream.readline(max_line_bytes + 1)
        if not line:
            return
        if len(line) > max_line_bytes:
            raise TarStreamError(f"NDJSON line exceeded {max_line_bytes} bytes in {member_name}")
        stripped = line.rstrip(b"\n")
        if stripped:
            yield stripped
