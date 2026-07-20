"""Mini layout renderer: Article -> RenderedEntry (TASK-H007/K004/K005/K009/L003).

ARCHITECTURE.md 16.2 describes the "標準レイアウト" this module renders.

Renders the "標準レイアウト" as plain text: title, aliases, update date, the
abstract, section-numbered body (1./1.1 style), categories, and source
license info. TableBlock render policy (16.3) covers all four complexity
tiers: "simple" as grid-like plain text (TASK-K004), "wide"/"complex" as
vertical label:value records (TASK-K005), and "unsupported" (no rows) as
just its caption. InfoboxBlock (TASK-K009) renders its title, each
field's flattened value, and a placeholder line per image reference
(actual image download/rendering is a separate epic). ReferencesBlock
(TASK-L003) renders each item as a numbered "[N] citation text" line, in
DOM order -- the only correspondence to an inline marker's number, since
the model carries no explicit id linkage (see TASK-L002). Entry size
budget splitting (16.4) remains out of scope -- no article this renderer
sees today can be oversized enough to need it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from wikiepwing.model.article import Article
from wikiepwing.model.blocks import (
    Block,
    CodeBlock,
    DefinitionListBlock,
    HeadingBlock,
    HorizontalRuleBlock,
    ImageBlock,
    InfoboxBlock,
    MathBlock,
    OrderedListBlock,
    ParagraphBlock,
    PreformattedBlock,
    QuoteBlock,
    ReferencesBlock,
    TableBlock,
    TableCell,
    UnorderedListBlock,
    UnsupportedBlock,
)
from wikiepwing.model.inline import Inline, InternalLinkInline, MathInline
from wikiepwing.render.entry_id import compute_entry_id
from wikiepwing.render.render_node import (
    GraphicRenderNode,
    LinkRenderNode,
    RenderNode,
    TextRenderNode,
)
from wikiepwing.render.rendered_entry import RenderedEntry


def render_article_to_entry(
    article: Article,
    *,
    headwords: tuple[str, ...] | None = None,
    graphic_names_by_media_id: dict[str, str] | None = None,
    keywords: tuple[str, ...] | None = None,
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

    graphic_names_by_url: dict[str, str] = {}
    if graphic_names_by_media_id:
        for media in article.media:
            gname = graphic_names_by_media_id.get(media.media_id)
            if gname:
                graphic_names_by_url[media.source_url] = gname
                if media.source_url.startswith("https:"):
                    graphic_names_by_url[media.source_url[6:]] = gname
                elif media.source_url.startswith("http:"):
                    graphic_names_by_url[media.source_url[5:]] = gname

    context = _RenderContext(
        graphic_names_by_media_id=graphic_names_by_media_id or {},
        graphic_names_by_url=graphic_names_by_url,
        captions_by_media_id={media.media_id: media.caption for media in article.media},
    )
    numberer = _HeadingNumberer()
    for block in article.blocks:
        lines.extend(_render_block(block, numberer, context=context, indent=0))

    if article.categories:
        lines.append("カテゴリ")
        lines.extend(article.categories)
        lines.append("")

    if article.source_license_ids:
        lines.append("出典情報")
        lines.extend(article.source_license_ids)

    body_text = "\n".join(lines).rstrip("\n")
    body = _parse_link_markers(body_text)

    if headwords is None:
        headwords = (article.title, *(alias.title for alias in article.aliases))
    internal_targets = tuple(
        dict.fromkeys(node.target for node in body if isinstance(node, LinkRenderNode))
    )
    graphics = tuple(
        dict.fromkeys(node.name for node in body if isinstance(node, GraphicRenderNode))
    )

    return RenderedEntry(
        entry_id=compute_entry_id(article.page_id),
        page_id=article.page_id,
        title=article.title,
        headwords=headwords,
        body=body,
        internal_targets=internal_targets,
        graphics=graphics,
        estimated_size=sum(_render_node_size(node) for node in body),
        diagnostics=article.diagnostics,
        keywords=keywords or (),
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


@dataclass(frozen=True, slots=True)
class _RenderContext:
    graphic_names_by_media_id: dict[str, str]
    graphic_names_by_url: dict[str, str]
    captions_by_media_id: dict[str, str | None]


def _render_block(
    block: Block, numberer: _HeadingNumberer, *, context: _RenderContext, indent: int
) -> list[str]:
    prefix = "  " * indent
    if isinstance(block, HeadingBlock):
        text = _flatten_inlines(block.inlines)
        return [f"■ {text}", ""]
    if isinstance(block, ParagraphBlock):
        text = _flatten_inlines(block.inlines)
        return [f"{prefix}{text}", ""] if text else [""]
    if isinstance(block, UnorderedListBlock | OrderedListBlock):
        lines: list[str] = []
        for index, item in enumerate(block.items, start=1):
            marker = "・" if isinstance(block, UnorderedListBlock) else f"{index}."
            item_lines: list[str] = []
            for child in item.blocks:
                item_lines.extend(
                    _render_block(child, numberer, context=context, indent=indent + 1)
                )
            if item_lines:
                item_lines[0] = f"{prefix}{marker} {_safe_strip(item_lines[0])}"
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
                    definitions.extend(
                        _render_block(child, numberer, context=context, indent=indent + 1)
                    )
            joined = " ".join(_safe_strip(line) for line in definitions if _safe_strip(line))
            lines.append(f"{prefix}{terms}: {joined}")
        lines.append("")
        return lines
    if isinstance(block, QuoteBlock):
        lines = []
        for child in block.blocks:
            lines.extend(_render_block(child, numberer, context=context, indent=indent + 1))
        return lines
    if isinstance(block, PreformattedBlock | CodeBlock):
        return [f"{prefix}{line}" for line in block.text.split("\n")] + [""]
    if isinstance(block, HorizontalRuleBlock):
        return ["----", ""]
    if isinstance(block, UnsupportedBlock):
        return [f"{prefix}{block.fallback_text}", ""] if block.fallback_text else [""]
    if isinstance(block, MathBlock):
        return [f"{prefix}{block.source}", ""]
    if isinstance(block, ImageBlock):
        caption = context.captions_by_media_id.get(block.media_id) or block.alt_text or "画像"
        graphic_name = context.graphic_names_by_media_id.get(block.media_id)
        if graphic_name is None:
            return [f"{prefix}[画像: {caption}]", ""]
        return [f"{prefix}\x1eG:{graphic_name}\x1f", f"{prefix}{caption}", ""]
    if isinstance(block, TableBlock):
        return _render_table(block, prefix)
    if isinstance(block, InfoboxBlock):
        return _render_infobox(block, prefix, context)
    if isinstance(block, ReferencesBlock):
        return _render_references(block, prefix)
    return [""]


def _render_references(block: ReferencesBlock, prefix: str) -> list[str]:
    lines = [
        f"{prefix}[{index}] {_flatten_inlines(item)}" for index, item in enumerate(block.items, 1)
    ]
    lines.append("")
    return lines


def _render_infobox(block: InfoboxBlock, prefix: str, context: _RenderContext) -> list[str]:
    lines: list[str] = []
    if block.title:
        lines.append(f"{prefix}【Infobox {block.title}】")
    else:
        lines.append(f"{prefix}【Infobox】")
    for field in block.fields:
        value_parts = [
            _safe_strip(line)
            for child in field.value
            for line in _render_block(child, _HeadingNumberer(), context=context, indent=0)
            if _safe_strip(line)
        ]
        val_str = " ".join(value_parts)
        lines.append(f"{prefix}【{field.name}|{val_str}】")
    for image_src in block.images:
        graphic_name = (
            context.graphic_names_by_url.get(image_src)
            or (
                context.graphic_names_by_url.get("https:" + image_src)
                if image_src.startswith("//")
                else None
            )
            or (
                context.graphic_names_by_url.get("//" + image_src)
                if not image_src.startswith("//") and not image_src.startswith("http")
                else None
            )
        )
        if graphic_name:
            lines.append(f"{prefix}\x1eG:{graphic_name}\x1f")
        else:
            lines.append(f"{prefix}【画像|{image_src}】")
    lines.append("")
    return lines


def _render_table(block: TableBlock, prefix: str) -> list[str]:
    lines: list[str] = []
    caption_text = _flatten_inlines(block.caption)
    if caption_text:
        lines.append(f"{prefix}{caption_text}")
    for row in block.rows:
        lines.append(prefix + " | ".join(_flatten_table_cell(cell) for cell in row))
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
            _safe_strip(line)
            for line in _render_block(
                child,
                _HeadingNumberer(),
                context=_RenderContext({}, {}, {}),
                indent=0,
            )
            if _safe_strip(line)
        )
    return " ".join(parts)


def _safe_strip(text: str) -> str:
    """Strip leading and trailing whitespace, preserving control codes 0x1e and 0x1f."""
    start = 0
    end = len(text)
    while start < end and text[start].isspace() and text[start] not in {"\x1e", "\x1f"}:
        start += 1
    while end > start and text[end - 1].isspace() and text[end - 1] not in {"\x1e", "\x1f"}:
        end -= 1
    return text[start:end]


def _flatten_inlines(inlines: tuple[Inline, ...]) -> str:
    return "".join(_inline_text(inline) for inline in inlines)


def _inline_text(inline: Inline) -> str:
    if isinstance(inline, MathInline):
        return inline.source
    if isinstance(inline, InternalLinkInline):
        link_label = _flatten_inlines(inline.label)
        if inline.resolution == "resolved" and inline.target_page_id is not None:
            target = compute_entry_id(inline.target_page_id)
            return f"\x1eR:{target}\x1f{link_label}\x1eE\x1f"
        return link_label
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


_BODY_MARKER = re.compile(
    r"\x1eR:(p[0-9]+)\x1f(.*?)\x1eE\x1f|\x1eG:([A-Za-z0-9_-]+)\x1f", re.DOTALL
)


def _parse_link_markers(text: str) -> tuple[RenderNode, ...]:
    nodes: list[RenderNode] = []
    position = 0
    for match in _BODY_MARKER.finditer(text):
        if match.start() > position:
            nodes.append(TextRenderNode(text=text[position : match.start()]))
        if match.group(3) is not None:
            nodes.append(GraphicRenderNode(name=match.group(3)))
        else:
            nodes.append(LinkRenderNode(label=match.group(2), target=match.group(1)))
        position = match.end()
    if position < len(text):
        nodes.append(TextRenderNode(text=text[position:]))
    if not nodes:
        nodes.append(TextRenderNode(text=""))
    return tuple(nodes)


def _render_node_size(node: RenderNode) -> int:
    if isinstance(node, TextRenderNode):
        return len(node.text.encode("utf-8"))
    if isinstance(node, LinkRenderNode):
        return len(node.label.encode("utf-8"))
    if isinstance(node, GraphicRenderNode):
        return 1
    return 1


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
