"""Deterministic archive packaging (TASK-S003, ARCHITECTURE.md 26.2, DATA_CONTRACTS.md 12).

26.2's determinism checklist includes "archive timestamp固定": ZIP entries
normally embed the wall-clock mtime of each source file, which alone
would make two content-identical builds produce different archive
bytes. `build_deterministic_archive` fixes every entry's timestamp to
one caller-supplied `archive_timestamp` (config's `[epwing]
archive_timestamp`), fixes each entry's permission bits, and adds files
in sorted relative-path order (filesystem iteration order is not
guaranteed stable) -- so re-running this over byte-identical input
always produces a byte-identical ZIP, matching DATA_CONTRACTS.md 12's
`<book-directory>/` internal root layout.
"""

from __future__ import annotations

import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

_FILE_PERMISSIONS = 0o644


def build_deterministic_archive(
    source_dir: Path,
    archive_path: Path,
    *,
    root_directory_name: str,
    archive_timestamp: datetime,
) -> None:
    """Package every file under `source_dir` into `archive_path` as a deterministic ZIP."""
    if archive_timestamp.tzinfo is None:
        raise ValueError("archive_timestamp must be timezone-aware")
    if not root_directory_name:
        raise ValueError("root_directory_name must be a non-empty string")

    date_time = (
        archive_timestamp.year,
        archive_timestamp.month,
        archive_timestamp.day,
        archive_timestamp.hour,
        archive_timestamp.minute,
        archive_timestamp.second,
    )
    files = sorted(path for path in source_dir.rglob("*") if path.is_file())

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=archive_path.parent, prefix=f".{archive_path.name}.", suffix=".tmp"
    )
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for file_path in files:
                relative = file_path.relative_to(source_dir)
                arcname = f"{root_directory_name}/{relative.as_posix()}"
                info = zipfile.ZipInfo(arcname, date_time=date_time)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = _FILE_PERMISSIONS << 16
                archive.writestr(info, file_path.read_bytes())
        os.replace(temporary_path, archive_path)
    finally:
        temporary_path.unlink(missing_ok=True)
