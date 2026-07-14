"""Block model: the initial subset from ARCHITECTURE.md 11.2 (PLAN.md Phase 5/6 scope).

Table/Infobox implement the full field set from ARCHITECTURE.md 11.5/11.6 now,
even though the HTML-to-Block conversion that populates them is deferred to
later epics (K/L). Image/Math/References are intentionally minimal placeholder
shapes (documented assumption: no concrete field spec exists yet); their real
structure is deferred to the epics that render them (O/N/L). NoticeBlock is
out of scope for this task (not part of PLAN.md's initial rollout list) and
can be added later as a non-breaking union extension.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from wikiepwing.model.inline import Inline, inline_payload, parse_inline

TableComplexity = Literal["simple", "wide", "complex", "unsupported"]
_TABLE_COMPLEXITIES = ("simple", "wide", "complex", "unsupported")


class BlockError(ValueError):
    """Raised when a Block cannot be constructed or decoded safely."""


@dataclass(frozen=True, slots=True)
class ParagraphBlock:
    """A paragraph of inline content."""

    inlines: tuple[Inline, ...]

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "paragraph", "inlines": [inline_payload(inline) for inline in self.inlines]}


@dataclass(frozen=True, slots=True)
class HeadingBlock:
    """A section heading."""

    level: int
    anchor: str
    inlines: tuple[Inline, ...]

    def __post_init__(self) -> None:
        if not 1 <= self.level <= 6:
            raise BlockError(f"level must be between 1 and 6: {self.level!r}")
        if not self.anchor:
            raise BlockError("anchor must be a non-empty string")

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {
            "type": "heading",
            "level": self.level,
            "anchor": self.anchor,
            "inlines": [inline_payload(inline) for inline in self.inlines],
        }


@dataclass(frozen=True, slots=True)
class ListItem:
    """One item of an ordered or unordered list, containing nested blocks."""

    blocks: tuple[Block, ...]

    def payload(self) -> dict[str, object]:
        """Return this list item's JSON-serializable representation."""
        return {"blocks": [block_payload(block) for block in self.blocks]}


@dataclass(frozen=True, slots=True)
class UnorderedListBlock:
    """A bulleted list."""

    items: tuple[ListItem, ...]

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "unordered_list", "items": [item.payload() for item in self.items]}


@dataclass(frozen=True, slots=True)
class OrderedListBlock:
    """A numbered list."""

    items: tuple[ListItem, ...]

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "ordered_list", "items": [item.payload() for item in self.items]}


@dataclass(frozen=True, slots=True)
class DefinitionEntry:
    """One term/definition group of a definition list."""

    terms: tuple[tuple[Inline, ...], ...]
    definitions: tuple[tuple[Block, ...], ...]

    def payload(self) -> dict[str, object]:
        """Return this entry's JSON-serializable representation."""
        return {
            "terms": [[inline_payload(inline) for inline in term] for term in self.terms],
            "definitions": [
                [block_payload(block) for block in definition] for definition in self.definitions
            ],
        }


@dataclass(frozen=True, slots=True)
class DefinitionListBlock:
    """A definition list (term/definition pairs)."""

    entries: tuple[DefinitionEntry, ...]

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "definition_list", "entries": [entry.payload() for entry in self.entries]}


@dataclass(frozen=True, slots=True)
class QuoteBlock:
    """A block quotation wrapping nested blocks."""

    blocks: tuple[Block, ...]

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "quote", "blocks": [block_payload(block) for block in self.blocks]}


@dataclass(frozen=True, slots=True)
class PreformattedBlock:
    """Preformatted text with no inline formatting applied."""

    text: str

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "preformatted", "text": self.text}


@dataclass(frozen=True, slots=True)
class CodeBlock:
    """A fenced code block."""

    text: str
    language: str | None

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "code", "text": self.text, "language": self.language}


@dataclass(frozen=True, slots=True)
class HorizontalRuleBlock:
    """A horizontal rule separator."""

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "horizontal_rule"}


@dataclass(frozen=True, slots=True)
class TableCell:
    """One cell of a TableBlock row (ARCHITECTURE.md 11.5)."""

    blocks: tuple[Block, ...]
    row_span: int
    col_span: int
    is_header: bool

    def __post_init__(self) -> None:
        if self.row_span < 1:
            raise BlockError(f"row_span must be >= 1: {self.row_span!r}")
        if self.col_span < 1:
            raise BlockError(f"col_span must be >= 1: {self.col_span!r}")

    def payload(self) -> dict[str, object]:
        """Return this cell's JSON-serializable representation."""
        return {
            "blocks": [block_payload(block) for block in self.blocks],
            "row_span": self.row_span,
            "col_span": self.col_span,
            "is_header": self.is_header,
        }


@dataclass(frozen=True, slots=True)
class TableBlock:
    """A table (ARCHITECTURE.md 11.5). HTML-to-Table conversion lands in a later epic."""

    caption: tuple[Inline, ...]
    rows: tuple[tuple[TableCell, ...], ...]
    source_class_names: tuple[str, ...]
    complexity: TableComplexity

    def __post_init__(self) -> None:
        if self.complexity not in _TABLE_COMPLEXITIES:
            raise BlockError(
                f"complexity must be one of {_TABLE_COMPLEXITIES}: {self.complexity!r}"
            )

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {
            "type": "table",
            "caption": [inline_payload(inline) for inline in self.caption],
            "rows": [[cell.payload() for cell in row] for row in self.rows],
            "source_class_names": list(self.source_class_names),
            "complexity": self.complexity,
        }


@dataclass(frozen=True, slots=True)
class InfoboxField:
    """One name/value field of an InfoboxBlock (ARCHITECTURE.md 11.6)."""

    name: str
    value: tuple[Block, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise BlockError("name must be a non-empty string")

    def payload(self) -> dict[str, object]:
        """Return this field's JSON-serializable representation."""
        return {"name": self.name, "value": [block_payload(block) for block in self.value]}


@dataclass(frozen=True, slots=True)
class InfoboxBlock:
    """An infobox (ARCHITECTURE.md 11.6). HTML-to-Infobox conversion lands in a later epic."""

    title: str | None
    fields: tuple[InfoboxField, ...]
    images: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {
            "type": "infobox",
            "title": self.title,
            "fields": [field.payload() for field in self.fields],
            "images": list(self.images),
        }


@dataclass(frozen=True, slots=True)
class ImageBlock:
    """A minimal image reference placeholder (documented assumption: no full spec yet)."""

    media_id: str
    alt_text: str | None

    def __post_init__(self) -> None:
        if not self.media_id:
            raise BlockError("media_id must be a non-empty string")

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "image", "media_id": self.media_id, "alt_text": self.alt_text}


@dataclass(frozen=True, slots=True)
class MathBlock:
    """A minimal block-level math placeholder (documented assumption: no full spec yet)."""

    source: str
    source_format: str

    def __post_init__(self) -> None:
        if not self.source_format:
            raise BlockError("source_format must be a non-empty string")

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {"type": "math", "source": self.source, "source_format": self.source_format}


@dataclass(frozen=True, slots=True)
class ReferencesBlock:
    """A minimal references/footnotes list placeholder (documented assumption: no full spec yet)."""

    items: tuple[tuple[Inline, ...], ...]

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {
            "type": "references",
            "items": [[inline_payload(inline) for inline in item] for item in self.items],
        }


@dataclass(frozen=True, slots=True)
class UnsupportedBlock:
    """A fallback for any block content not yet modeled explicitly."""

    element_name: str
    fallback_text: str
    diagnostic_code: str

    def __post_init__(self) -> None:
        if not self.element_name:
            raise BlockError("element_name must be a non-empty string")
        if not self.diagnostic_code:
            raise BlockError("diagnostic_code must be a non-empty string")

    def payload(self) -> dict[str, object]:
        """Return this block's JSON-serializable representation."""
        return {
            "type": "unsupported",
            "element_name": self.element_name,
            "fallback_text": self.fallback_text,
            "diagnostic_code": self.diagnostic_code,
        }


Block = (
    ParagraphBlock
    | HeadingBlock
    | UnorderedListBlock
    | OrderedListBlock
    | DefinitionListBlock
    | QuoteBlock
    | PreformattedBlock
    | CodeBlock
    | HorizontalRuleBlock
    | TableBlock
    | InfoboxBlock
    | ImageBlock
    | MathBlock
    | ReferencesBlock
    | UnsupportedBlock
)


def block_payload(block: Block) -> dict[str, object]:
    """Return any Block's JSON-serializable representation."""
    return block.payload()


def parse_block(payload: object) -> Block:
    """Parse one JSON object into a Block. Unknown `type` values are a codec error."""
    if not isinstance(payload, dict):
        raise BlockError("block must be a JSON object")
    fields = cast(dict[str, object], payload)
    kind = fields.get("type")
    if kind == "paragraph":
        return ParagraphBlock(inlines=_parse_inline_list(fields, "inlines"))
    if kind == "heading":
        return HeadingBlock(
            level=_require_int(fields, "level"),
            anchor=_require_str(fields, "anchor"),
            inlines=_parse_inline_list(fields, "inlines"),
        )
    if kind == "unordered_list":
        return UnorderedListBlock(items=_parse_list_items(fields, "items"))
    if kind == "ordered_list":
        return OrderedListBlock(items=_parse_list_items(fields, "items"))
    if kind == "definition_list":
        return DefinitionListBlock(entries=_parse_definition_entries(fields, "entries"))
    if kind == "quote":
        return QuoteBlock(blocks=_parse_block_list(fields, "blocks"))
    if kind == "preformatted":
        return PreformattedBlock(text=_require_str(fields, "text"))
    if kind == "code":
        return CodeBlock(
            text=_require_str(fields, "text"),
            language=_optional_str(fields, "language"),
        )
    if kind == "horizontal_rule":
        return HorizontalRuleBlock()
    if kind == "table":
        return TableBlock(
            caption=_parse_inline_list(fields, "caption"),
            rows=_parse_table_rows(fields, "rows"),
            source_class_names=_parse_str_list(fields, "source_class_names"),
            complexity=cast(TableComplexity, _require_str(fields, "complexity")),
        )
    if kind == "infobox":
        return InfoboxBlock(
            title=_optional_str(fields, "title"),
            fields=_parse_infobox_fields(fields, "fields"),
            images=_parse_str_list(fields, "images"),
        )
    if kind == "image":
        return ImageBlock(
            media_id=_require_str(fields, "media_id"),
            alt_text=_optional_str(fields, "alt_text"),
        )
    if kind == "math":
        return MathBlock(
            source=_require_str(fields, "source"),
            source_format=_require_str(fields, "source_format"),
        )
    if kind == "references":
        return ReferencesBlock(items=_parse_inline_list_list(fields, "items"))
    if kind == "unsupported":
        return UnsupportedBlock(
            element_name=_require_str(fields, "element_name"),
            fallback_text=_optional_str(fields, "fallback_text") or "",
            diagnostic_code=_require_str(fields, "diagnostic_code"),
        )
    raise BlockError(f"unknown block type: {kind!r}")


def _require_str(fields: dict[str, object], key: str) -> str:
    value = fields.get(key)
    if not isinstance(value, str):
        raise BlockError(f"block is missing a string field: {key}")
    return value


def _optional_str(fields: dict[str, object], key: str) -> str | None:
    value = fields.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise BlockError(f"block field {key} must be a string or null")
    return value


def _require_int(fields: dict[str, object], key: str) -> int:
    value = fields.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise BlockError(f"block is missing an integer field: {key}")
    return value


def _parse_str_list(fields: dict[str, object], key: str) -> tuple[str, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise BlockError(f"block is missing an array field: {key}")
    items = cast(list[object], value)
    for item in items:
        if not isinstance(item, str):
            raise BlockError(f"block field {key} must be an array of strings")
    return tuple(cast(list[str], items))


def _parse_inline_list(fields: dict[str, object], key: str) -> tuple[Inline, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise BlockError(f"block is missing an array field: {key}")
    return tuple(parse_inline(item) for item in cast(list[object], value))


def _parse_inline_list_list(fields: dict[str, object], key: str) -> tuple[tuple[Inline, ...], ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise BlockError(f"block is missing an array field: {key}")
    result = []
    for item in cast(list[object], value):
        if not isinstance(item, list):
            raise BlockError(f"block field {key} must be an array of arrays")
        result.append(tuple(parse_inline(inline) for inline in cast(list[object], item)))
    return tuple(result)


def _parse_block_list(fields: dict[str, object], key: str) -> tuple[Block, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise BlockError(f"block is missing an array field: {key}")
    return tuple(parse_block(item) for item in cast(list[object], value))


def _parse_list_items(fields: dict[str, object], key: str) -> tuple[ListItem, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise BlockError(f"block is missing an array field: {key}")
    items = []
    for item in cast(list[object], value):
        if not isinstance(item, dict):
            raise BlockError("list item must be a JSON object")
        item_fields = cast(dict[str, object], item)
        items.append(ListItem(blocks=_parse_block_list(item_fields, "blocks")))
    return tuple(items)


def _parse_definition_entries(fields: dict[str, object], key: str) -> tuple[DefinitionEntry, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise BlockError(f"block is missing an array field: {key}")
    entries = []
    for item in cast(list[object], value):
        if not isinstance(item, dict):
            raise BlockError("definition entry must be a JSON object")
        entry_fields = cast(dict[str, object], item)
        entries.append(
            DefinitionEntry(
                terms=_parse_inline_list_list(entry_fields, "terms"),
                definitions=_parse_block_list_list(entry_fields, "definitions"),
            )
        )
    return tuple(entries)


def _parse_block_list_list(fields: dict[str, object], key: str) -> tuple[tuple[Block, ...], ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise BlockError(f"block is missing an array field: {key}")
    result = []
    for item in cast(list[object], value):
        if not isinstance(item, list):
            raise BlockError(f"block field {key} must be an array of arrays")
        result.append(tuple(parse_block(block) for block in cast(list[object], item)))
    return tuple(result)


def _parse_table_rows(fields: dict[str, object], key: str) -> tuple[tuple[TableCell, ...], ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise BlockError(f"block is missing an array field: {key}")
    rows = []
    for row in cast(list[object], value):
        if not isinstance(row, list):
            raise BlockError(f"block field {key} must be an array of arrays")
        cells = []
        for cell in cast(list[object], row):
            if not isinstance(cell, dict):
                raise BlockError("table cell must be a JSON object")
            cell_fields = cast(dict[str, object], cell)
            cells.append(
                TableCell(
                    blocks=_parse_block_list(cell_fields, "blocks"),
                    row_span=_require_int(cell_fields, "row_span"),
                    col_span=_require_int(cell_fields, "col_span"),
                    is_header=_require_bool(cell_fields, "is_header"),
                )
            )
        rows.append(tuple(cells))
    return tuple(rows)


def _parse_infobox_fields(fields: dict[str, object], key: str) -> tuple[InfoboxField, ...]:
    value = fields.get(key)
    if not isinstance(value, list):
        raise BlockError(f"block is missing an array field: {key}")
    result = []
    for item in cast(list[object], value):
        if not isinstance(item, dict):
            raise BlockError("infobox field must be a JSON object")
        item_fields = cast(dict[str, object], item)
        result.append(
            InfoboxField(
                name=_require_str(item_fields, "name"),
                value=_parse_block_list(item_fields, "value"),
            )
        )
    return tuple(result)


def _require_bool(fields: dict[str, object], key: str) -> bool:
    value = fields.get(key)
    if not isinstance(value, bool):
        raise BlockError(f"block is missing a boolean field: {key}")
    return value
