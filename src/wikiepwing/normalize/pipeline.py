"""End-to-end HTML-to-Block pipeline (TASK-G012), tying together TASK-G001-G011.

`normalize_html` runs: safe parse (G001) -> root content selection (G002) ->
unsafe/UI node removal (G003) -> document assembly with unknown-DOM fallback
(G004-G010) -> whitespace normalization (G011) -> body media extraction/role
classification (TASK-O012, wiring TASK-O001-O002's `classify_body_media`).

`images_enabled` (TASK-P004, ARCHITECTURE.md 21.3's "同じコードパスを使い、
profile設定で差を作ります") is the one config-driven behavior difference
this pipeline currently applies: when the `[images]` section's `enabled`
is false (the Mini profile's `mini.toml`), body media extraction is
skipped entirely and `normalize/orchestrate.py` skips reading the
Snapshot's main image too, so `Article.media` ends up empty -- matching
21.1's "imageなし" for Mini -- rather than scattering `if profile ==
"mini"` checks through the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.model.article import MediaReference
from wikiepwing.model.blocks import Block
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.convert_block import convert_document
from wikiepwing.normalize.html_parser import parse_html
from wikiepwing.normalize.media_extraction import classify_body_media
from wikiepwing.normalize.root_selection import select_root_content
from wikiepwing.normalize.unsafe_nodes import UnsafeNodeRemovalOptions, remove_unsafe_nodes
from wikiepwing.normalize.whitespace import normalize_block_whitespace


@dataclass(frozen=True, slots=True)
class NormalizeOptions:
    """The subset of `[normalize]` configuration this pipeline consumes."""

    max_dom_depth: int
    html_recover: bool
    remove_edit_ui: bool
    remove_navboxes: bool
    remove_authority_control: bool
    images_enabled: bool = True

    def _removal_options(self) -> UnsafeNodeRemovalOptions:
        return UnsafeNodeRemovalOptions(
            remove_edit_ui=self.remove_edit_ui,
            remove_navboxes=self.remove_navboxes,
            remove_authority_control=self.remove_authority_control,
        )


def normalize_html(
    html: str, options: NormalizeOptions
) -> tuple[tuple[Block, ...], tuple[MediaReference, ...], tuple[Diagnostic, ...]]:
    """Convert one article's raw HTML into normalized Blocks, body media, and diagnostics."""
    diagnostics: list[Diagnostic] = []

    parse_result = parse_html(
        html, max_dom_depth=options.max_dom_depth, html_recover=options.html_recover
    )
    diagnostics.extend(parse_result.diagnostics)

    root_children = select_root_content(parse_result.root)

    filtered_children, removal_diagnostics = remove_unsafe_nodes(
        root_children, options._removal_options()
    )
    diagnostics.extend(removal_diagnostics)

    blocks, document_diagnostics = convert_document(filtered_children)
    diagnostics.extend(document_diagnostics)

    normalized_blocks = tuple(normalize_block_whitespace(block) for block in blocks)
    body_media = classify_body_media(filtered_children) if options.images_enabled else ()

    return normalized_blocks, body_media, tuple(diagnostics)
