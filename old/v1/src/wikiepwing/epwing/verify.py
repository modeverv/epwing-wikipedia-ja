"""Independent structural checks for packaged EPWING artifacts."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Inspection:
    ok: bool
    members: tuple[str, ...]
    errors: tuple[str, ...]


def inspect_archive(path: Path) -> Inspection:
    """Check the minimum package structure without trusting generation success."""
    try:
        with zipfile.ZipFile(path) as archive:
            members = tuple(sorted(archive.namelist()))
    except (OSError, zipfile.BadZipFile) as error:
        return Inspection(False, (), (f"ARCHIVE_INVALID: {error}",))
    errors: list[str] = []
    if "CATALOGS" not in members:
        errors.append("CATALOG_MISSING")
    if "TOOLCHAIN.json" not in members:
        errors.append("TOOLCHAIN_MANIFEST_MISSING")
    if not any(member.endswith("/DATA/HONMON.ebz") for member in members):
        errors.append("COMPRESSED_HONMON_MISSING")
    return Inspection(not errors, members, tuple(errors))
