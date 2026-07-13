"""Prepare conservative EPWING color graphics from extracted image references."""

from __future__ import annotations

import base64
import hashlib
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from PIL import Image, UnidentifiedImageError

TOKEN = re.compile(r"@@IMAGE:([A-Za-z0-9_-]+):([A-Za-z0-9_-]*)@@")
MAX_DOWNLOAD_BYTES = 8 * 1024 * 1024
MAX_DIMENSION = 4096
THUMBNAIL_SIZE = (320, 240)
USER_AGENT = "wikiepwing/0.1 local EPWING image resolver"


@dataclass(frozen=True, slots=True)
class GraphicResult:
    resolved: int
    failed: int
    references: int


def _decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode()).decode()


def _graphic_name(file_name: str) -> str:
    digest = hashlib.sha1(file_name.casefold().encode()).hexdigest()[:16]
    return f"img-{digest}"


def _download_url(file_name: str) -> str:
    quoted = urllib.parse.quote(file_name.replace(" ", "_"), safe="")
    return f"https://commons.wikimedia.org/wiki/Special:Redirect/file/{quoted}?width=320"


def _fetch_image(file_name: str) -> bytes:
    request = urllib.request.Request(_download_url(file_name), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        content_type = response.headers.get("Content-Type", "")
        if not content_type.lower().startswith("image/"):
            raise ValueError(f"not an image response: {content_type}")
        data = response.read(MAX_DOWNLOAD_BYTES + 1)
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise ValueError("image download exceeds size limit")
    return cast(bytes, data)


def _write_bmp(data: bytes, destination: Path) -> None:
    from io import BytesIO

    with Image.open(BytesIO(data)) as image:
        if image.width > MAX_DIMENSION or image.height > MAX_DIMENSION:
            raise ValueError("image dimensions exceed limit")
        image.thumbnail(THUMBNAIL_SIZE)
        canvas = Image.new("RGB", image.size, "white")
        if image.mode in {"RGBA", "LA"}:
            canvas.paste(image.convert("RGBA"), mask=image.convert("RGBA").getchannel("A"))
        else:
            canvas.paste(image.convert("RGB"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(destination, format="BMP")


def materialize_graphics(
    records: Path, destination: Path, limit: int, forced_files: tuple[str, ...] = ()
) -> GraphicResult:
    """Download selected images, create cgraph definitions, and rewrite image tokens."""
    destination.mkdir(parents=True, exist_ok=True)
    image_dir = destination / "images"
    cgraphs = destination / "cgraphs.txt"
    report = destination / "image-report.tsv"
    image_dir.mkdir(parents=True, exist_ok=True)
    selected: dict[str, str] = {file_name: _graphic_name(file_name) for file_name in forced_files}
    references = 0
    failed = 0

    with records.open("r", encoding="utf-8") as reader:
        for line in reader:
            for match in TOKEN.finditer(line):
                references += 1
                file_name = _decode(match.group(1))
                if file_name not in selected and len(selected) < limit + len(forced_files):
                    selected.setdefault(file_name, _graphic_name(file_name))

    rows: list[str] = []
    resolved: dict[str, str] = {}
    for file_name, name in selected.items():
        bmp = image_dir / f"{name}.bmp"
        try:
            _write_bmp(_fetch_image(file_name), bmp)
        except (
            OSError,
            TimeoutError,
            urllib.error.URLError,
            UnidentifiedImageError,
            ValueError,
        ) as error:
            failed += 1
            rows.append(f"FAILED\t{name}\t{file_name}\t{error}\n")
            continue
        resolved[file_name] = name
        rows.append(f"OK\t{name}\t{file_name}\n")

    with cgraphs.open("w", encoding="utf-8") as target:
        for name in resolved.values():
            target.write(f"{name}\timages/{name}.bmp\n")
    with report.open("w", encoding="utf-8") as target:
        target.writelines(rows)

    temporary = records.with_suffix(records.suffix + ".graphics")
    with (
        records.open("r", encoding="utf-8") as reader,
        temporary.open("w", encoding="utf-8") as writer,
    ):
        for line in reader:
            def replace(match: re.Match[str]) -> str:
                file_name = _decode(match.group(1))
                name = resolved.get(file_name)
                if not name:
                    return f"[image] {file_name}"
                return f"@@CGRAPH:{name}@@"

            writer.write(TOKEN.sub(replace, line))
    temporary.replace(records)
    return GraphicResult(len(resolved), failed, references)
