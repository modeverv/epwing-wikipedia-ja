"""Bounded, non-mutating metadata inventory for reference EPWING books."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

from wikiepwing.reference.scanner import (
    ReferencePathError,
    read_only_status,
    validate_reference_path,
)

INVENTORY_SCHEMA_VERSION = 1
MAX_INVENTORY_DEPTH = 16
MAX_INVENTORY_ENTRIES = 100_000
MAX_RELATIVE_PATH_BYTES = 4096


class ReferenceInventoryError(ValueError):
    """Raised when a safe and complete reference inventory cannot be produced."""


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    """One non-dereferenced filesystem entry below a reference root."""

    path: str
    kind: str
    size_bytes: int | None

    def payload(self) -> dict[str, object]:
        """Return this entry in its stable JSON representation."""
        return {"kind": self.kind, "path": self.path, "size_bytes": self.size_bytes}


@dataclass(frozen=True, slots=True)
class SubbookCandidate:
    """A directory with a recognizable EPWING HONMON payload."""

    catalog_path: str
    directory: str
    name: str
    honmon_paths: tuple[str, ...]
    gaiji_paths: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        """Return this candidate in its stable JSON representation."""
        return {
            "catalog_path": self.catalog_path,
            "directory": self.directory,
            "gaiji_paths": list(self.gaiji_paths),
            "honmon_paths": list(self.honmon_paths),
            "name": self.name,
        }


@dataclass(frozen=True, slots=True)
class ReferenceInventory:
    """Complete bounded metadata inventory for one validated reference root."""

    root: Path
    entries: tuple[InventoryEntry, ...]
    subbook_candidates: tuple[SubbookCandidate, ...]

    def payload(self) -> dict[str, object]:
        """Return the schema-versioned, deterministic JSON representation."""
        counts = {kind: 0 for kind in ("directory", "file", "symlink", "other")}
        total_file_bytes = 0
        for entry in self.entries:
            counts[entry.kind] += 1
            if entry.kind == "file" and entry.size_bytes is not None:
                total_file_bytes += entry.size_bytes
        return {
            "entries": [entry.payload() for entry in self.entries],
            "root": str(self.root),
            "schema_version": INVENTORY_SCHEMA_VERSION,
            "subbook_candidates": [candidate.payload() for candidate in self.subbook_candidates],
            "summary": {
                "directory_count": counts["directory"],
                "file_count": counts["file"],
                "other_count": counts["other"],
                "symlink_count": counts["symlink"],
                "total_file_bytes": total_file_bytes,
            },
        }


def build_reference_inventory(
    root: Path,
    *,
    max_depth: int = MAX_INVENTORY_DEPTH,
    max_entries: int = MAX_INVENTORY_ENTRIES,
    max_path_bytes: int = MAX_RELATIVE_PATH_BYTES,
) -> ReferenceInventory:
    """Inventory a validated reference root without following links or reading payloads."""
    _validate_limits(max_depth, max_entries, max_path_bytes)
    try:
        validation = validate_reference_path(root)
    except ReferencePathError as error:
        raise ReferenceInventoryError(str(error)) from error

    entries: list[InventoryEntry] = []
    pending: list[Path] = [validation.root]
    while pending:
        directory = pending.pop()
        try:
            children = sorted(
                os.scandir(directory), key=lambda entry: (entry.name.casefold(), entry.name)
            )
        except OSError as error:
            raise ReferenceInventoryError(
                f"cannot inventory directory: {directory}: {error}"
            ) from error
        child_directories: list[Path] = []
        for child in children:
            relative = Path(child.path).relative_to(validation.root).as_posix()
            depth = len(Path(relative).parts)
            if depth > max_depth:
                raise ReferenceInventoryError(
                    f"reference inventory depth limit {max_depth} exceeded: {relative}"
                )
            if len(relative.encode("utf-8")) > max_path_bytes:
                raise ReferenceInventoryError(
                    f"reference inventory path byte limit {max_path_bytes} exceeded: {relative}"
                )
            if len(entries) >= max_entries:
                raise ReferenceInventoryError(
                    f"reference inventory entry limit {max_entries} exceeded"
                )
            try:
                child_status = child.stat(follow_symlinks=False)
            except OSError as error:
                raise ReferenceInventoryError(
                    f"cannot inspect reference entry: {relative}: {error}"
                ) from error

            child_path = Path(child.path)
            if stat.S_ISLNK(child_status.st_mode):
                entries.append(InventoryEntry(relative, "symlink", None))
            elif stat.S_ISDIR(child_status.st_mode):
                _require_read_only(child_path, relative)
                entries.append(InventoryEntry(relative, "directory", None))
                child_directories.append(child_path)
            elif stat.S_ISREG(child_status.st_mode):
                _require_read_only(child_path, relative)
                entries.append(InventoryEntry(relative, "file", child_status.st_size))
            else:
                entries.append(InventoryEntry(relative, "other", None))
        pending.extend(reversed(child_directories))

    entries.sort(key=lambda entry: (entry.path.casefold(), entry.path))
    candidates = _find_subbook_candidates(validation.root, validation.catalogs, entries)
    return ReferenceInventory(validation.root, tuple(entries), candidates)


def write_reference_inventory(inventory: ReferenceInventory, output: Path) -> Path:
    """Atomically write a stable JSON report outside the reference root."""
    destination = output.expanduser().resolve(strict=False)
    if destination == inventory.root or inventory.root in destination.parents:
        raise ReferenceInventoryError(
            f"inventory output must be outside reference root: {destination}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = (
        json.dumps(inventory.payload(), ensure_ascii=False, indent=2, sort_keys=True).encode(
            "utf-8"
        )
        + b"\n"
    )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
        ) as temporary:
            temporary.write(document)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        temporary_path.replace(destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return destination


def _validate_limits(max_depth: int, max_entries: int, max_path_bytes: int) -> None:
    if max_depth < 1:
        raise ReferenceInventoryError("max_depth must be positive")
    if max_entries < 1:
        raise ReferenceInventoryError("max_entries must be positive")
    if max_path_bytes < 1:
        raise ReferenceInventoryError("max_path_bytes must be positive")


def _require_read_only(path: Path, relative: str) -> None:
    try:
        read_only, detail = read_only_status(path)
    except ReferencePathError as error:
        raise ReferenceInventoryError(str(error)) from error
    if not read_only:
        raise ReferenceInventoryError(f"reference entry must be read-only: {relative}: {detail}")


def _find_subbook_candidates(
    root: Path,
    catalogs: tuple[Path, ...],
    entries: list[InventoryEntry],
) -> tuple[SubbookCandidate, ...]:
    files = tuple(entry.path for entry in entries if entry.kind == "file")
    candidates: list[SubbookCandidate] = []
    for catalog in catalogs:
        catalog_relative = catalog.relative_to(root).as_posix()
        catalog_parent = catalog.parent.relative_to(root)
        by_directory: dict[str, list[str]] = {}
        for file_path in files:
            relative_path = Path(file_path)
            try:
                below_catalog = relative_path.relative_to(catalog_parent)
            except ValueError:
                continue
            parts = below_catalog.parts
            if len(parts) < 2 or parts[-1].casefold() not in {"honmon", "honmon.ebz"}:
                continue
            if len(parts) > 2 and parts[1].casefold() != "data":
                continue
            directory = (catalog_parent / parts[0]).as_posix()
            by_directory.setdefault(directory, []).append(file_path)
        for directory, honmon_paths in by_directory.items():
            directory_prefix = f"{directory}/"
            gaiji_paths = tuple(
                sorted(
                    (
                        file_path
                        for file_path in files
                        if file_path.startswith(directory_prefix)
                        and "gaiji" in (part.casefold() for part in Path(file_path).parts)
                    ),
                    key=lambda path: (path.casefold(), path),
                )
            )
            candidates.append(
                SubbookCandidate(
                    catalog_path=catalog_relative,
                    directory=directory,
                    name=Path(directory).name,
                    honmon_paths=tuple(
                        sorted(honmon_paths, key=lambda path: (path.casefold(), path))
                    ),
                    gaiji_paths=gaiji_paths,
                )
            )
    candidates.sort(
        key=lambda candidate: (
            candidate.catalog_path.casefold(),
            candidate.directory.casefold(),
            candidate.directory,
        )
    )
    return tuple(candidates)
