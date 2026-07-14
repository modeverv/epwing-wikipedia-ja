"""Definition list conversion (TASK-G008, ARCHITECTURE.md 12.2 pass N60).

Converts `<dl>` into `DefinitionListBlock`. Consecutive `<dt>` elements are
grouped as one entry's terms; the `<dd>` elements that follow become that
entry's definitions. A new `<dt>` seen after at least one `<dd>` has already
been collected starts a new entry.
"""

from __future__ import annotations

from wikiepwing.model.blocks import Block, DefinitionEntry, DefinitionListBlock, ParagraphBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import Inline
from wikiepwing.normalize.html_parser import ElementNode, Node
from wikiepwing.normalize.paragraphs import convert_inline_nodes


def is_definition_list(node: Node) -> bool:
    """Return whether `node` is a `<dl>` element."""
    return isinstance(node, ElementNode) and node.tag == "dl"


def convert_definition_list(
    node: ElementNode,
) -> tuple[DefinitionListBlock, tuple[Diagnostic, ...]]:
    """Convert one `<dl>` element into a DefinitionListBlock."""
    if node.tag != "dl":
        raise ValueError(f"not a definition list element: <{node.tag}>")

    entries: list[DefinitionEntry] = []
    current_terms: list[tuple[Inline, ...]] = []
    current_definitions: list[tuple[Block, ...]] = []

    def flush() -> None:
        if current_terms or current_definitions:
            entries.append(
                DefinitionEntry(terms=tuple(current_terms), definitions=tuple(current_definitions))
            )
            current_terms.clear()
            current_definitions.clear()

    for child in node.children:
        if not isinstance(child, ElementNode):
            continue
        if child.tag == "dt":
            if current_definitions:
                flush()
            current_terms.append(convert_inline_nodes(child.children))
        elif child.tag == "dd":
            current_definitions.append(
                (ParagraphBlock(inlines=convert_inline_nodes(child.children)),)
            )
    flush()

    return DefinitionListBlock(entries=tuple(entries)), ()
