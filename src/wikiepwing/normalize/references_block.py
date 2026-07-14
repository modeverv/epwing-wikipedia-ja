"""Build a ReferencesBlock from a `<ol class="references">` element (TASK-L003).

Converts each of TASK-L002's `RawReferenceItem`s into an `Inline` sequence
(`wikiepwing.normalize.paragraphs.convert_inline_nodes`) to assemble the
model `ReferencesBlock` (ARCHITECTURE.md 11.2's Block union). `note_id` is
not carried into the block -- `ReferencesBlock.items` has no id field
(TASK-L002's docstring already covers why) -- so item order is the only
correspondence between a rendered reference and the inline markers that
cite it.
"""

from __future__ import annotations

from wikiepwing.model.blocks import ReferencesBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.html_parser import ElementNode
from wikiepwing.normalize.paragraphs import convert_inline_nodes
from wikiepwing.normalize.reference_list import parse_reference_list


def build_references_block(node: ElementNode) -> tuple[ReferencesBlock, tuple[Diagnostic, ...]]:
    """Parse and convert one `<ol class="references">` element into a ReferencesBlock."""
    items = tuple(convert_inline_nodes(item.content) for item in parse_reference_list(node))
    return ReferencesBlock(items=items), ()
