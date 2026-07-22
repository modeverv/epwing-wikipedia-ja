"""FreePWING source generation: RenderedEntry -> intermediate JSON Lines (TASK-H009).

ARCHITECTURE.md 17.2 assigns "FreePWING source file生成" and "graphic/gaiji
登録" to the FreePWING adapter. This module produces the plain intermediate
data file (one JSON object per line: tag/title/aliases/body/targets) that
`docker/toolchain/freepwing_build_entries.pl` reads to drive the actual
`FreePWING::FPWUtils::FPWParser` Perl API calls -- and, per 17.2's
"graphic/gaiji登録" responsibility, resolves every non-backend-representable
character (`wikiepwing.gaiji.embedding`, GAIJI.md) before it ever reaches
that file, since title/aliases/body are the only strings that flow into the
toolchain's EUC-JP-only text. HTML parsing, table flattening, alias
extraction, and text normalization are explicitly *not* this adapter's job
(17.2's non-responsibilities) -- they already happened upstream in the
normalize/render pipeline; gaiji resolution operates only on the flattened
strings those upstream stages already produced.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import cast

from wikiepwing.gaiji.embedding import (
    GaijiPlan,
    embed_gaiji_tokens,
    embed_title_fallback,
    plan_gaiji_codes,
)
from wikiepwing.gaiji.unrepresentable import UnrepresentableTracker
from wikiepwing.pipeline.progress import PhaseProgress
from wikiepwing.render.render_node import (
    GraphicRenderNode,
    LineBreakRenderNode,
    LinkRenderNode,
    RenderNode,
    TextRenderNode,
)
from wikiepwing.render.rendered_entry import RenderedEntry


def write_entries_jsonl_stream(
    entries_generator: Callable[[], Iterable[RenderedEntry]],
    destination: Path,
    *,
    tracker: UnrepresentableTracker | None = None,
    on_progress: Callable[[PhaseProgress], None] | None = None,
) -> GaijiPlan:
    """Write entries yielded by `entries_generator` as FreePWING build input stream.

    Scans bodies in a first pass, plans gaiji codes, then encodes and writes JSONL
    atomically in a second pass to keep memory usage bounded (Phase 8 vertical slice).
    """
    total = 0

    def scan_bodies() -> Iterable[str]:
        nonlocal total
        _report(on_progress, "generate-entry-records", 0, 0)
        for entry in entries_generator():
            total += 1
            _report(on_progress, "generate-entry-records", total, total)
            yield cast(str, _entry_record(entry)["body"])

    plan = plan_gaiji_codes(
        scan_bodies(),
        on_progress=(
            None
            if on_progress is None
            else lambda completed, _: _report(on_progress, "generate-gaiji-scan", completed, total)
        ),
        total=total,
    )

    if total == 0:
        _report(on_progress, "generate-gaiji-embedding", 0, 0)
        _report(on_progress, "generate-json-encoding", 0, 0)
    else:
        _report(on_progress, "generate-gaiji-embedding", 0, total)

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_destination = destination.with_suffix(".tmp")
    try:
        with temp_destination.open("w", encoding="utf-8") as out:
            for index, entry in enumerate(entries_generator(), start=1):
                record = _entry_record(entry)
                record["title"] = embed_title_fallback(
                    cast(str, record["title"]),
                    tracker=tracker,
                    page_id=entry.page_id,
                    title=entry.title,
                )
                record["heading"] = embed_title_fallback(
                    cast(str, record["heading"]),
                    tracker=tracker,
                    page_id=entry.page_id,
                    title=entry.title,
                )
                record["aliases"] = [
                    embed_title_fallback(
                        alias, tracker=tracker, page_id=entry.page_id, title=entry.title
                    )
                    for alias in cast(list[str], record["aliases"])
                ]
                record["keywords"] = [
                    embed_title_fallback(
                        kw, tracker=tracker, page_id=entry.page_id, title=entry.title
                    )
                    for kw in cast(list[str], record["keywords"])
                ]
                record["body"] = embed_gaiji_tokens(
                    cast(str, record["body"]),
                    plan=plan,
                    tracker=tracker,
                    page_id=entry.page_id,
                    title=entry.title,
                )
                _report(on_progress, "generate-gaiji-embedding", index, total)

                line = json.dumps(record, ensure_ascii=False)
                out.write(f"{line}\n")
                _report(on_progress, "generate-json-encoding", index, total)

        _report(on_progress, "generate-entries-write", 0, 1)
        os.replace(temp_destination, destination)
        _report(on_progress, "generate-entries-write", 1, 1)
    except BaseException:
        if temp_destination.is_file():
            temp_destination.unlink()
        raise

    return plan


def _report(
    callback: Callable[[PhaseProgress], None] | None,
    phase: str,
    completed: int,
    total: int,
) -> None:
    if callback is not None:
        callback(
            PhaseProgress(
                phase=phase,
                completed=completed,
                total=total,
                unit="items",
                complete=completed >= total,
            )
        )


def _entry_record(entry: RenderedEntry) -> dict[str, object]:
    body_text = "".join(_serialize_body_node(node) for node in entry.body)
    aliases = [headword for headword in entry.headwords[1:]]
    return {
        "tag": entry.entry_id,
        "title": entry.title,
        "heading": entry.heading or entry.title,
        "aliases": aliases,
        "keywords": list(entry.keywords),
        "body": body_text,
        "targets": list(entry.internal_targets),
    }


def _serialize_body_node(node: RenderNode) -> str:
    if isinstance(node, TextRenderNode):
        return node.text
    if isinstance(node, LinkRenderNode):
        return f"\x1eR:{node.target}\x1f{node.label}\x1eE\x1f"
    if isinstance(node, GraphicRenderNode):
        return f"\x1eG:{node.name}\x1f"
    if isinstance(node, LineBreakRenderNode):
        return "\n"
    raise TypeError(f"unsupported render node: {type(node).__name__}")
