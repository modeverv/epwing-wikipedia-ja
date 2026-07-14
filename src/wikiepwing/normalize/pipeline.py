"""End-to-end HTML-to-Block pipeline (TASK-G012), tying together TASK-G001-G011.

`normalize_html` runs: safe parse (G001) -> root content selection (G002) ->
unsafe/UI node removal (G003) -> document assembly with unknown-DOM fallback
(G004-G010) -> whitespace normalization (G011).
"""

from __future__ import annotations

from dataclasses import dataclass

from wikiepwing.model.blocks import Block
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.convert_block import convert_document
from wikiepwing.normalize.html_parser import parse_html
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

    def _removal_options(self) -> UnsafeNodeRemovalOptions:
        return UnsafeNodeRemovalOptions(
            remove_edit_ui=self.remove_edit_ui,
            remove_navboxes=self.remove_navboxes,
            remove_authority_control=self.remove_authority_control,
        )


def normalize_html(
    html: str, options: NormalizeOptions
) -> tuple[tuple[Block, ...], tuple[Diagnostic, ...]]:
    """Convert one article's raw HTML into normalized Blocks, plus all diagnostics found."""
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

    return normalized_blocks, tuple(diagnostics)
