"""Disk usage reporting (TASK-S007, PLAN.md 29's `wikiepwing disk-usage`).

`compute_disk_usage` sums the on-disk size of every `config.paths`
directory (sources/reference/work/cache/output/reports/logs) so an
operator can see where space is going before running `clean`
(TASK-S008) or a fresh `update` (TASK-S006). A missing directory
reports `exists=False`/`size_bytes=0` rather than raising -- most of
these paths don't exist until their stage has actually run.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from wikiepwing.config import AppConfig


@dataclass(frozen=True, slots=True)
class PathUsage:
    """One named path's on-disk size."""

    name: str
    path: Path
    exists: bool
    size_bytes: int

    def payload(self) -> dict[str, object]:
        """Return this path usage's JSON-serializable representation."""
        return {
            "name": self.name,
            "path": str(self.path),
            "exists": self.exists,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class DiskUsageReport:
    """Disk usage across every configured path, plus free space on the work volume."""

    paths: tuple[PathUsage, ...]
    total_bytes: int
    free_bytes: int

    def payload(self) -> dict[str, object]:
        """Return this report's JSON-serializable representation."""
        return {
            "schema_version": 1,
            "paths": [path.payload() for path in self.paths],
            "total_bytes": self.total_bytes,
            "free_bytes": self.free_bytes,
        }


def compute_disk_usage(config: AppConfig) -> DiskUsageReport:
    """Compute on-disk usage for every path in `config.paths`."""
    named_paths = (
        ("sources", config.paths.sources),
        ("reference", config.paths.reference),
        ("work", config.paths.work),
        ("cache", config.paths.cache),
        ("output", config.paths.output),
        ("reports", config.paths.reports),
        ("logs", config.paths.logs),
    )
    usages = tuple(
        PathUsage(
            name=name,
            path=path,
            exists=path.exists(),
            size_bytes=_directory_size(path) if path.exists() else 0,
        )
        for name, path in named_paths
    )
    total_bytes = sum(usage.size_bytes for usage in usages)

    free_root = next((path for _name, path in named_paths if path.exists()), None)
    free_bytes = shutil.disk_usage(free_root).free if free_root is not None else 0

    return DiskUsageReport(paths=usages, total_bytes=total_bytes, free_bytes=free_bytes)


def _directory_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file() and not entry.is_symlink():
            total += entry.stat().st_size
    return total
