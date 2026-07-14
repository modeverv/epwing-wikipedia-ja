"""FreePWING source generation: RenderedEntry -> intermediate JSON Lines (TASK-H009).

ARCHITECTURE.md 17.2 assigns "FreePWING source file生成" to the FreePWING
adapter. This module only produces a plain intermediate data file (one JSON
object per line: tag/title/aliases/body/targets); the actual
`FreePWING::FPWUtils::FPWParser` Perl API calls that build the `fpwmake`
source tree run inside the toolchain Docker image via
`docker/toolchain/freepwing_build_entries.pl`, which reads this file. HTML
parsing, table flattening, alias extraction, and text normalization are
explicitly *not* this adapter's job (17.2's non-responsibilities) -- they
already happened upstream in the normalize/render pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

from wikiepwing.pipeline.atomic_write import atomic_write_text
from wikiepwing.render.render_node import TextRenderNode
from wikiepwing.render.rendered_entry import RenderedEntry


def write_entries_jsonl(entries: tuple[RenderedEntry, ...], destination: Path) -> None:
    """Write `entries` as FreePWING build input: one JSON object per line, atomically."""
    lines = (json.dumps(_entry_record(entry), ensure_ascii=False) for entry in entries)
    text = "".join(f"{line}\n" for line in lines)
    atomic_write_text(destination, text)


def _entry_record(entry: RenderedEntry) -> dict[str, object]:
    body_text = "\n".join(node.text for node in entry.body if isinstance(node, TextRenderNode))
    aliases = [headword for headword in entry.headwords[1:]]
    return {
        "tag": entry.entry_id,
        "title": entry.title,
        "aliases": aliases,
        "body": body_text,
        "targets": list(entry.internal_targets),
    }
