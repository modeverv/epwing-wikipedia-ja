"""Deterministic full-width EPWING gaiji generation."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TOKEN = re.compile(r"@@GAIJI:([a-z0-9-]+)@@")
# FreePWING's FullUserChar implementation encodes an 8192-character limit.
MAX_GAIJI = 8192


@dataclass(frozen=True, slots=True)
class GaijiResult:
    names: tuple[str, ...]
    replacements: int
    overflow_names: tuple[str, ...]
    overflow_replacements: int
    title_replacements: int


def gaiji_name(character: str) -> str:
    """Return a deterministic ASCII identifier for one Unicode scalar."""
    return f"u-{ord(character):x}"


@cache
def needs_gaiji(character: str) -> bool:
    """Return whether a character cannot be emitted in FreePWING's EUC-JP text."""
    try:
        encoded = character.encode("euc_jp")
    except UnicodeEncodeError:
        return True
    return encoded.startswith(b"\x8f")


def _font_path() -> Path:
    candidates = (
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("no configured CJK font is available for gaiji rendering")


def _write_xbm(character: str, destination: Path) -> None:
    image = Image.new("1", (16, 16), 1)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(_font_path()), 15, index=0)
    box = draw.textbbox((0, 0), character, font=font)
    width, height = box[2] - box[0], box[3] - box[1]
    position = ((16 - width) // 2 - box[0], (16 - height) // 2 - box[1])
    draw.text(position, character, font=font, fill=0)
    image.save(destination, format="XBM")


def _body_characters(records: Path) -> Iterator[str]:
    """Yield unencodable body characters without changing title search keys."""
    with records.open("r", encoding="utf-8") as reader:
        for line in reader:
            _title, separator, body = line.partition("\t")
            if separator:
                yield from (character for character in body if needs_gaiji(character))


def materialize_gaiji(records: Path, destination: Path) -> GaijiResult:
    """Create at most FreePWING's supported gaiji set without silent loss.

    Less frequent unsupported scalars are written as ASCII ``[U+XXXX]`` text and
    reported in ``gaiji-overflow.txt``.  This preserves the source identity even
    when the legacy EPWING user-character table is full.
    """
    destination.mkdir(parents=True, exist_ok=True)
    transformed = records.with_suffix(records.suffix + ".gaiji")
    counts = Counter(_body_characters(records))
    selected_characters = set(
        sorted(counts, key=lambda character: (-counts[character], ord(character)))[:MAX_GAIJI]
    )
    names: dict[str, str] = {
        gaiji_name(character): character for character in selected_characters
    }
    overflow: dict[str, str] = {
        gaiji_name(character): character
        for character in counts
        if character not in selected_characters
    }
    replacements = 0
    overflow_replacements = 0
    title_replacements = 0
    title_overflow: Counter[str] = Counter()
    with records.open("r", encoding="utf-8") as reader, transformed.open(
        "w", encoding="utf-8"
    ) as writer:
        for line in reader:
            title, separator, body = line.partition("\t")
            if not separator:
                writer.write(line)
                continue
            converted_title: list[str] = []
            for character in title:
                if needs_gaiji(character):
                    converted_title.append(f"[U+{ord(character):04X}]")
                    title_overflow[character] += 1
                    title_replacements += 1
                else:
                    converted_title.append(character)
            converted: list[str] = []
            for character in body:
                if needs_gaiji(character):
                    name = gaiji_name(character)
                    if character in selected_characters:
                        converted.append(f"@@GAIJI:{name}@@")
                        replacements += 1
                    else:
                        converted.append(f"[U+{ord(character):04X}]")
                        overflow_replacements += 1
                else:
                    converted.append(character)
            writer.write("".join(converted_title) + separator + "".join(converted))
    transformed.replace(records)
    for name, character in sorted(names.items()):
        _write_xbm(character, destination / f"{name}16.xbm")
    (destination.parent / "fullchar.txt").write_text(
        "".join(f"{name} gaiji/{name}16.xbm\n" for name in sorted(names)), encoding="ascii"
    )
    (destination.parent / "gaiji-overflow.txt").write_text(
        "".join(
            f"BODY\t{name}\tU+{ord(character):04X}\t{counts[character]}\n"
            for name, character in sorted(overflow.items())
        )
        + "".join(
            f"TITLE\t{gaiji_name(character)}\tU+{ord(character):04X}\t{count}\n"
            for character, count in sorted(title_overflow.items())
        ),
        encoding="ascii",
    )
    return GaijiResult(
        tuple(sorted(names)),
        replacements,
        tuple(sorted(overflow)),
        overflow_replacements,
        title_replacements,
    )
