"""Build an InfoboxBlock from a `<table>` element (TASK-K009, ARCHITECTURE.md 11.6).

Chains TASK-K008's `parse_infobox_dom` and converts each field's raw value
nodes into `Block`s (`wikiepwing.normalize.convert_block.convert_document`,
the same helper TASK-K004 uses for table cells) to assemble the actual
model `InfoboxBlock`/`InfoboxField`. An infobox with no title, no fields,
and no images records an `INFOBOX_EMPTY` diagnostic (ARCHITECTURE.md 11.7's
example code list already names it) rather than silently producing an
empty block.
"""

from __future__ import annotations

from wikiepwing.model.blocks import InfoboxBlock, InfoboxField
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.convert_block import convert_document
from wikiepwing.normalize.html_parser import ElementNode
from wikiepwing.normalize.infobox_fields import parse_infobox_dom


def build_infobox_block(table_element: ElementNode) -> tuple[InfoboxBlock, tuple[Diagnostic, ...]]:
    """Parse and convert one infobox `<table>` element into an InfoboxBlock."""
    raw_infobox, raw_diagnostics = parse_infobox_dom(table_element)
    diagnostics: list[Diagnostic] = list(raw_diagnostics)

    fields = []
    for raw_field in raw_infobox.fields:
        blocks, field_diagnostics = convert_document(raw_field.value_nodes)
        diagnostics.extend(field_diagnostics)
        fields.append(InfoboxField(name=raw_field.name, value=blocks))

    infobox = InfoboxBlock(
        title=raw_infobox.title,
        fields=tuple(fields),
        images=raw_infobox.image_srcs,
    )
    if infobox.title is None and not infobox.fields and not infobox.images:
        diagnostics.append(_empty_diagnostic())

    return infobox, tuple(diagnostics)


def _empty_diagnostic() -> Diagnostic:
    return Diagnostic(
        code="INFOBOX_EMPTY",
        severity="warning",
        stage="normalize_infobox",
        page_id=None,
        title=None,
        message="infobox has no title, fields, or images",
        source_path=None,
        source_excerpt=None,
        details={},
    )
