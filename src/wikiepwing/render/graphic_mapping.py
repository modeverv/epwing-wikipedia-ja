"""Load the source-URL to FreePWING graphic-name mapping for generate."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import cast

_MAX_REPORT_BYTES = 256 * 1024 * 1024
_MAX_URL_LENGTH = 16_384
_CONTENT_HASH = re.compile(r"^[0-9a-f]{64}$")


class GraphicMappingError(ValueError):
    """Raised when image conversion metadata is unsafe or inconsistent."""


def load_graphic_names_by_media_id(report_path: Path, graphics_dir: Path) -> dict[str, str]:
    """Return successful report URLs whose content hash exists in cgraphs.txt."""
    size = report_path.stat().st_size
    if size > _MAX_REPORT_BYTES:
        raise GraphicMappingError(f"image report exceeds {_MAX_REPORT_BYTES} bytes")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise GraphicMappingError("image report must be a JSON array")
    available = _read_catalog_names(graphics_dir / "cgraphs.txt")
    mapping: dict[str, str] = {}
    for raw_item in payload:
        if not isinstance(raw_item, dict):
            raise GraphicMappingError("image report item must be an object")
        item = cast(dict[str, object], raw_item)
        if item.get("ok") is not True:
            continue
        source_url = item.get("source_url")
        content_hash = item.get("content_hash")
        if not isinstance(source_url, str) or not 0 < len(source_url) <= _MAX_URL_LENGTH:
            raise GraphicMappingError("successful image report item has an invalid source_url")
        if not isinstance(content_hash, str) or not _CONTENT_HASH.fullmatch(content_hash):
            raise GraphicMappingError("successful image report item has an invalid content_hash")
        if content_hash in available:
            mapping[source_url] = content_hash
    return mapping


def _read_catalog_names(path: Path) -> frozenset[str]:
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 2 or not _CONTENT_HASH.fullmatch(fields[0]):
            raise GraphicMappingError(f"invalid graphics catalog line: {line!r}")
        names.add(fields[0])
    return frozenset(names)
