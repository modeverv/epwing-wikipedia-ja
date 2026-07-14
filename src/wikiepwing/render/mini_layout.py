"""Mini layout renderer: Article -> RenderedEntry (TASK-H007/K004/K005/K009, ARCHITECTURE.md 16.2).

Renders the "標準レイアウト" as plain text: title, aliases, update date, the
abstract, section-numbered body (1./1.1 style), categories, and source
license info. TableBlock render policy (16.3) covers all four complexity
tiers: "simple" as grid-like plain text (TASK-K004), "wide"/"complex" as
vertical label:value records (TASK-K005), and "unsupported" (no rows) as
just its caption. InfoboxBlock (TASK-K009) renders its title, each
field's flattened value, and a placeholder line per image reference
(actual image download/rendering is a separate epic). Entry size budget
splitting (16.4) remains out of scope -- no article this renderer sees
today can be oversized enough to need it.
"""

from __future__ import annotations

from wikiepwing.model.article import Article
from wikiepwing.model.blocks import (
    Block,
    CodeBlock,
    DefinitionListBlock,
    HeadingBlock,
    HorizontalRuleBlock,
    InfoboxBlock,
    OrderedListBlock,
    ParagraphBlock,
    PreformattedBlock,
    QuoteBlock,
    TableBlock,
    TableCell,
    UnorderedListBlock,
    UnsupportedBlock,
)
from wikiepwing.model.inline import Inline, InternalLinkInline
from wikiepwing.render.entry_id import compute_entry_id
from wikiepwing.render.render_node import RenderNode, TextRenderNode
from wikiepwing.render.rendered_entry import RenderedEntry


def render_article_to_entry(
    article: Article, *, headwords: tuple[str, ...] | None = None
) -> RenderedEntry:
    """Render one Article into a Mini-profile RenderedEntry.

    `headwords` overrides the default title-plus-aliases headword list.
    TASK-J007's `wikiepwing.search.backend_mapping.headwords_for_articles`
    supplies a collision-resolved list (title/redirect/variant SearchTerms,
    TASK-H008/J001-J006) built across every article in a build; callers
    that don't need that (e.g. single-article tests) can omit it.
    """
    lines: list[str] = [article.title]
    if article.aliases:
        lines.append("別名: " + "、".join(alias.title for alias in article.aliases))
    lines.append(f"更新: {article.source_date_modified:%Y-%m-%d}")
    lines.append("")

    if article.abstract:
        lines.append(article.abstract)
        lines.append("")

    numberer = _HeadingNumberer()
    for block in article.blocks:
        lines.extend(_render_block(block, numberer, indent=0))

    if article.categories:
        lines.append("カテゴリ")
        lines.extend(article.categories)
        lines.append("")

    if article.source_license_ids:
        lines.append("出典情報")
        lines.extend(article.source_license_ids)

    body_text = "\n".join(lines).rstrip("\n")
    body: tuple[RenderNode, ...] = (TextRenderNode(text=body_text),)

    if headwords is None:
        headwords = (article.title, *(alias.title for alias in article.aliases))
    internal_targets = _extract_internal_targets(article.blocks)

    return RenderedEntry(
        entry_id=compute_entry_id(article.page_id),
        page_id=article.page_id,
        title=article.title,
        headwords=headwords,
        body=body,
        internal_targets=internal_targets,
        graphics=(),
        estimated_size=len(body_text.encode("utf-8")),
        diagnostics=article.diagnostics,
    )


class _HeadingNumberer:
    """Assigns 1./1.1-style section numbers, tracking sibling/nesting depth."""

    def __init__(self) -> None:
        self._levels: list[int] = []
        self._path: list[int] = []

    def number_for(self, level: int) -> str:
        while self._levels and self._levels[-1] > level:
            self._levels.pop()
            self._path.pop()
        if self._levels and self._levels[-1] == level:
            self._path[-1] += 1
        else:
            self._levels.append(level)
            self._path.append(1)
        return ".".join(str(n) for n in self._path)


def _render_block(block: Block, numberer: _HeadingNumberer, *, indent: int) -> list[str]:
    prefix = "  " * indent
    if isinstance(block, HeadingBlock):
        number = numberer.number_for(block.level)
        text = _flatten_inlines(block.inlines)
        return [f"{number} {text}", ""]
    if isinstance(block, ParagraphBlock):
        text = _flatten_inlines(block.inlines)
        return [f"{prefix}{text}", ""] if text else [""]
    if isinstance(block, UnorderedListBlock | OrderedListBlock):
        lines: list[str] = []
        for index, item in enumerate(block.items, start=1):
            marker = "-" if isinstance(block, UnorderedListBlock) else f"{index}."
            item_lines: list[str] = []
            for child in item.blocks:
                item_lines.extend(_render_block(child, numberer, indent=indent + 1))
            if item_lines:
                item_lines[0] = f"{prefix}{marker} {item_lines[0].strip()}"
            lines.extend(item_lines)
        lines.append("")
        return lines
    if isinstance(block, DefinitionListBlock):
        lines = []
        for entry in block.entries:
            terms = "、".join(_flatten_inlines(term) for term in entry.terms)
            definitions: list[str] = []
            for definition in entry.definitions:
                for child in definition:
                    definitions.extend(_render_block(child, numberer, indent=indent + 1))
            joined = " ".join(line.strip() for line in definitions if line.strip())
            lines.append(f"{prefix}{terms}: {joined}")
        lines.append("")
        return lines
    if isinstance(block, QuoteBlock):
        lines = []
        for child in block.blocks:
            lines.extend(_render_block(child, numberer, indent=indent + 1))
        return lines
    if isinstance(block, PreformattedBlock | CodeBlock):
        return [f"{prefix}{line}" for line in block.text.split("\n")] + [""]
    if isinstance(block, HorizontalRuleBlock):
        return ["----", ""]
    if isinstance(block, UnsupportedBlock):
        return [f"{prefix}{block.fallback_text}", ""] if block.fallback_text else [""]
    if isinstance(block, TableBlock):
        return _render_table(block, prefix)
    if isinstance(block, InfoboxBlock):
        return _render_infobox(block, prefix)
    return [""]


def _render_infobox(block: InfoboxBlock, prefix: str) -> list[str]:
    lines: list[str] = []
    if block.title:
        lines.append(f"{prefix}{block.title}")
    for field in block.fields:
        value_parts = [
            line.strip()
            for child in field.value
            for line in _render_block(child, _HeadingNumberer(), indent=0)
            if line.strip()
        ]
        lines.append(f"{prefix}{field.name}: {' '.join(value_parts)}")
    for image_src in block.images:
        lines.append(f"{prefix}[画像: {image_src}]")
    lines.append("")
    return lines


def _render_table(block: TableBlock, prefix: str) -> list[str]:
    lines: list[str] = []
    caption_text = _flatten_inlines(block.caption)
    if caption_text:
        lines.append(f"{prefix}{caption_text}")
    if block.complexity == "simple":
        for row in block.rows:
            lines.append(prefix + " | ".join(_flatten_table_cell(cell) for cell in row))
    elif block.complexity in ("wide", "complex"):
        lines.extend(_render_table_as_records(block, prefix))
    lines.append("")
    return lines


def _render_table_as_records(block: TableBlock, prefix: str) -> list[str]:
    """Render each row as a vertical "label: value" record (ARCHITECTURE.md 16.3 wide/complex).

    If the first row is entirely header cells, its text becomes each
    subsequent row's field labels; otherwise cells fall back to generic
    "列N" labels. Cells from a merged (rowspan/colspan) table are expanded
    in DOM order without recomputing their exact grid position -- this
    task keeps the mapping simple rather than pairing every cell with the
    grid position TASK-K002 could resolve.
    """
    rows = block.rows
    header_labels: list[str] | None = None
    if rows and rows[0] and all(cell.is_header for cell in rows[0]):
        header_labels = [_flatten_table_cell(cell) for cell in rows[0]]
        rows = rows[1:]

    lines: list[str] = []
    for row in rows:
        for index, cell in enumerate(row):
            label = (
                header_labels[index]
                if header_labels is not None and index < len(header_labels)
                else f"列{index + 1}"
            )
            lines.append(f"{prefix}{label}: {_flatten_table_cell(cell)}")
        lines.append("")
    return lines


def _flatten_table_cell(cell: TableCell) -> str:
    parts: list[str] = []
    for child in cell.blocks:
        parts.extend(
            line.strip()
            for line in _render_block(child, _HeadingNumberer(), indent=0)
            if line.strip()
        )
    return " ".join(parts)


def _flatten_inlines(inlines: tuple[Inline, ...]) -> str:
    return "".join(_inline_text(inline) for inline in inlines)


def _inline_text(inline: Inline) -> str:
    value = getattr(inline, "value", None)
    if isinstance(value, str):
        return value
    if inline.__class__.__name__ == "LineBreakInline":
        return "\n"
    nested = getattr(inline, "inlines", None)
    if nested is not None:
        return _flatten_inlines(nested)
    label = getattr(inline, "label", None)
    if label is not None:
        return _flatten_inlines(label)
    fallback_text = getattr(inline, "fallback_text", None)
    if isinstance(fallback_text, str):
        return fallback_text
    return ""


def _extract_internal_targets(blocks: tuple[Block, ...]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for block in blocks:
        for link in _links_in_block(block):
            if link.resolution == "resolved" and link.target_page_id is not None:
                seen.setdefault(compute_entry_id(link.target_page_id), None)
    return tuple(seen)


def _links_in_block(block: Block) -> list[InternalLinkInline]:
    links: list[InternalLinkInline] = []
    inlines = getattr(block, "inlines", None)
    if inlines is not None:
        links.extend(_links_in_inlines(inlines))
    for child in _child_blocks(block):
        links.extend(_links_in_block(child))
    return links


def _child_blocks(block: Block) -> tuple[Block, ...]:
    children: list[Block] = []
    if isinstance(block, UnorderedListBlock | OrderedListBlock):
        for item in block.items:
            children.extend(item.blocks)
    if isinstance(block, DefinitionListBlock):
        for entry in block.entries:
            for definition in entry.definitions:
                children.extend(definition)
    if isinstance(block, QuoteBlock):
        children.extend(block.blocks)
    return tuple(children)


def _links_in_inlines(inlines: tuple[Inline, ...]) -> list[InternalLinkInline]:
    links: list[InternalLinkInline] = []
    for inline in inlines:
        if isinstance(inline, InternalLinkInline):
            links.append(inline)
            links.extend(_links_in_inlines(inline.label))
        else:
            nested = getattr(inline, "inlines", None)
            if nested is not None:
                links.extend(_links_in_inlines(nested))
    return links
