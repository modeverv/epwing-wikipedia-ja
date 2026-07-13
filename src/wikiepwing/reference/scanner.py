"""Non-mutating validation and bounded CATALOGS discovery for reference books."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

MAX_CATALOG_BYTES = 1024 * 1024
MAX_SCAN_DEPTH = 4
MAX_VISITED_ENTRIES = 10_000
EPWING_BLOCK_BYTES = 2048


class ReferencePathError(ValueError):
    """Raised when a reference root cannot be inspected safely as read-only data."""


@dataclass(frozen=True, slots=True)
class ReferencePathValidation:
    """Validated reference root and its discovered EPWING catalogs."""

    root: Path
    catalogs: tuple[Path, ...]
    visited_entries: int


def read_only_status(path: Path) -> tuple[bool, str]:
    """Inspect read-only evidence without creating or modifying a file."""
    try:
        file_status = path.stat(follow_symlinks=False)
        filesystem_status = os.statvfs(path)
    except OSError as error:
        raise ReferencePathError(f"cannot inspect path permissions: {path}: {error}") from error

    read_only_flag = getattr(os, "ST_RDONLY", 1)
    if filesystem_status.f_flag & read_only_flag:
        return True, "filesystem is read-only"
    write_bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    if file_status.st_mode & write_bits == 0:
        return True, "write mode bits are disabled"
    if not os.access(path, os.W_OK):
        return True, "current process has no write access"
    return False, "path is writable"


def validate_reference_path(
    root: Path,
    *,
    max_depth: int = MAX_SCAN_DEPTH,
    max_visited_entries: int = MAX_VISITED_ENTRIES,
) -> ReferencePathValidation:
    """Validate a read-only reference root and discover regular CATALOGS files."""
    if not root.is_absolute():
        raise ReferencePathError(f"reference root must be absolute: {root}")
    try:
        root_status = root.lstat()
    except OSError as error:
        raise ReferencePathError(f"cannot inspect reference root: {root}: {error}") from error
    if stat.S_ISLNK(root_status.st_mode):
        raise ReferencePathError(f"reference root must not be a symlink: {root}")
    if not stat.S_ISDIR(root_status.st_mode):
        raise ReferencePathError(f"reference root must be a directory: {root}")
    resolved_root = root.resolve(strict=True)
    read_only, detail = read_only_status(resolved_root)
    if not read_only:
        raise ReferencePathError(f"reference root must be read-only: {resolved_root}: {detail}")
    if max_depth < 0:
        raise ReferencePathError("max_depth must not be negative")
    if max_visited_entries < 1:
        raise ReferencePathError("max_visited_entries must be positive")

    catalogs: list[Path] = []
    pending: list[tuple[Path, int]] = [(resolved_root, 0)]
    visited_entries = 0
    while pending:
        directory, depth = pending.pop()
        try:
            entries = sorted(
                os.scandir(directory), key=lambda entry: (entry.name.casefold(), entry.name)
            )
        except OSError as error:
            raise ReferencePathError(
                f"cannot scan reference directory: {directory}: {error}"
            ) from error
        for entry in entries:
            visited_entries += 1
            if visited_entries > max_visited_entries:
                raise ReferencePathError(
                    f"reference scan exceeds {max_visited_entries} directory entries"
                )
            if entry.is_symlink():
                continue
            entry_path = Path(entry.path)
            if entry.is_dir(follow_symlinks=False):
                entry_read_only, entry_detail = read_only_status(entry_path)
                if not entry_read_only:
                    raise ReferencePathError(
                        f"reference directory must be read-only: {entry_path}: {entry_detail}"
                    )
                if depth < max_depth:
                    pending.append((entry_path, depth + 1))
                continue
            if entry.name.casefold() != "catalogs" or not entry.is_file(follow_symlinks=False):
                continue
            catalog_read_only, catalog_detail = read_only_status(entry_path)
            if not catalog_read_only:
                raise ReferencePathError(
                    f"CATALOGS must be read-only: {entry_path}: {catalog_detail}"
                )
            size = entry.stat(follow_symlinks=False).st_size
            if size == 0 or size > MAX_CATALOG_BYTES or size % EPWING_BLOCK_BYTES != 0:
                raise ReferencePathError(f"invalid CATALOGS size {size}: {entry_path}")
            catalogs.append(entry_path.resolve(strict=True))

    if not catalogs:
        raise ReferencePathError(f"no regular CATALOGS file found under: {resolved_root}")
    catalogs.sort(
        key=lambda path: (path.relative_to(resolved_root).as_posix().casefold(), str(path))
    )
    return ReferencePathValidation(resolved_root, tuple(catalogs), visited_entries)
