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
from pathlib import Path
from typing import cast

from wikiepwing.gaiji.embedding import (
    GaijiPlan,
    embed_gaiji_tokens,
    embed_title_fallback,
    plan_gaiji_codes,
)
from wikiepwing.gaiji.unrepresentable import UnrepresentableTracker
from wikiepwing.pipeline.atomic_write import atomic_write_text
from wikiepwing.render.render_node import TextRenderNode
from wikiepwing.render.rendered_entry import RenderedEntry


def write_entries_jsonl(
    entries: tuple[RenderedEntry, ...],
    destination: Path,
    *,
    tracker: UnrepresentableTracker | None = None,
) -> GaijiPlan:
    """Write `entries` as FreePWING build input: one JSON object per line, atomically.

    Every distinct gaiji candidate character across every entry's title,
    aliases, and body is planned (TASK-M006's deterministic, processing-order
    -independent assignment) before any record is rewritten, then each
    record's body gets `@@GAIJI:<code>@@` placeholder tokens for those
    characters (`docker/toolchain/freepwing_build_entries.pl` turns them into
    real gaiji references) while title/aliases get the plain `[U+XXXX]`
    fallback instead (never a gaiji token -- see `wikiepwing.gaiji.embedding`).
    Returns the `GaijiPlan` so the caller can render the matching gaiji
    build files (XBM bitmaps + halfchars.txt/fullchars.txt).
    """
    records = [_entry_record(entry) for entry in entries]
    plan = plan_gaiji_codes(cast(str, record["body"]) for record in records)
    for entry, record in zip(entries, records, strict=True):
        record["title"] = embed_title_fallback(
            cast(str, record["title"]), tracker=tracker, page_id=entry.page_id, title=entry.title
        )
        record["aliases"] = [
            embed_title_fallback(alias, tracker=tracker, page_id=entry.page_id, title=entry.title)
            for alias in cast(list[str], record["aliases"])
        ]
        record["body"] = embed_gaiji_tokens(
            cast(str, record["body"]),
            plan=plan,
            tracker=tracker,
            page_id=entry.page_id,
            title=entry.title,
        )
    lines = (json.dumps(record, ensure_ascii=False) for record in records)
    text = "".join(f"{line}\n" for line in lines)
    atomic_write_text(destination, text)
    return plan


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
