from __future__ import annotations

import json
from pathlib import Path

import pytest

from wikiepwing.render.graphic_mapping import GraphicMappingError, load_graphic_names_by_media_id


def test_loads_only_successful_converted_graphics(tmp_path: Path) -> None:
    converted_hash = "a" * 64
    unconverted_hash = "b" * 64
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            [
                {"ok": True, "source_url": "//upload/flag.png", "content_hash": converted_hash},
                {
                    "ok": True,
                    "source_url": "//upload/missing.png",
                    "content_hash": unconverted_hash,
                },
                {"ok": False, "source_url": "//upload/failed.png", "content_hash": None},
            ]
        ),
        encoding="utf-8",
    )
    graphics = tmp_path / "graphics"
    graphics.mkdir()
    (graphics / "cgraphs.txt").write_text(
        f"{converted_hash} {converted_hash}.bmp\n", encoding="utf-8"
    )

    assert load_graphic_names_by_media_id(report, graphics) == {"//upload/flag.png": converted_hash}


def test_rejects_invalid_catalog_name(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text("[]", encoding="utf-8")
    graphics = tmp_path / "graphics"
    graphics.mkdir()
    (graphics / "cgraphs.txt").write_text("unsafe/name image.bmp\n", encoding="utf-8")

    with pytest.raises(GraphicMappingError, match="invalid graphics catalog"):
        load_graphic_names_by_media_id(report, graphics)
