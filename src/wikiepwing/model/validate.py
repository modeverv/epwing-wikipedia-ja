"""Model-layer Article validation (ARCHITECTURE.md 24.3, PLAN.md Phase 5 exit criteria).

Structural invariants already guaranteed by dataclass construction (title not
empty, block union shape, unknown `type` rejected by the codec) are not
re-checked here. This validator covers invariants that construction alone
cannot enforce: nesting depth limits, InternalLinkInline resolution/page_id
consistency, and embedded Diagnostic/Article identity consistency.

Corpus-wide invariants (e.g. unique page IDs across articles) are out of
scope: this validator only ever sees one Article at a time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from wikiepwing.config import AppConfig
from wikiepwing.model.article import Article
from wikiepwing.model.blocks import (
    Block,
    DefinitionListBlock,
    InfoboxBlock,
    ListItem,
    OrderedListBlock,
    QuoteBlock,
    TableBlock,
    UnorderedListBlock,
)
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import Inline, InternalLinkInline


class ModelValidationConfigError(ValueError):
    """Raised when model validation limits themselves are invalid."""


@dataclass(frozen=True, slots=True)
class ModelValidationLimits:
    """Configured limits used to validate one Article."""

    max_block_nesting_depth: int

    def __post_init__(self) -> None:
        if self.max_block_nesting_depth < 1:
            raise ModelValidationConfigError("max_block_nesting_depth must be positive")

    @classmethod
    def from_config(cls, config: AppConfig) -> ModelValidationLimits:
        """Build limits from the `[model]` configuration section."""
        model = config.section("model")
        return cls(max_block_nesting_depth=cast(int, model["max_block_nesting_depth"]))


def validate_article(article: Article, limits: ModelValidationLimits) -> tuple[Diagnostic, ...]:
    """Validate one Article's cross-field invariants. Returns diagnostics found (may be empty)."""
    diagnostics: list[Diagnostic] = []

    for block in article.blocks:
        _check_block_nesting(block, 1, limits.max_block_nesting_depth, article, diagnostics)
        _check_internal_links_in_block(block, article, diagnostics)

    for diagnostic in article.diagnostics:
        _check_diagnostic_consistency(diagnostic, article, diagnostics)

    return tuple(diagnostics)


def _check_block_nesting(
    block: Block,
    depth: int,
    max_depth: int,
    article: Article,
    diagnostics: list[Diagnostic],
) -> None:
    if depth > max_depth:
        diagnostics.append(
            _make_diagnostic(
                code="MODEL_BLOCK_NESTING_TOO_DEEP",
                article=article,
                message=f"block nesting exceeded {max_depth} at depth {depth}",
                details={"max_depth": max_depth, "depth": depth},
            )
        )
        return

    for child in _child_blocks(block):
        _check_block_nesting(child, depth + 1, max_depth, article, diagnostics)


def _child_blocks(block: Block) -> tuple[Block, ...]:
    if isinstance(block, UnorderedListBlock | OrderedListBlock):
        return tuple(child for item in block.items for child in _list_item_blocks(item))
    if isinstance(block, DefinitionListBlock):
        return tuple(
            child
            for entry in block.entries
            for definition in entry.definitions
            for child in definition
        )
    if isinstance(block, QuoteBlock):
        return block.blocks
    if isinstance(block, TableBlock):
        return tuple(child for row in block.rows for cell in row for child in cell.blocks)
    if isinstance(block, InfoboxBlock):
        return tuple(child for field in block.fields for child in field.value)
    return ()


def _list_item_blocks(item: ListItem) -> tuple[Block, ...]:
    return item.blocks


def _check_internal_links_in_block(
    block: Block, article: Article, diagnostics: list[Diagnostic]
) -> None:
    for inline in _block_inlines(block):
        _check_internal_links_in_inline(inline, article, diagnostics)
    for child in _child_blocks(block):
        _check_internal_links_in_block(child, article, diagnostics)


def _block_inlines(block: Block) -> tuple[Inline, ...]:
    inlines = getattr(block, "inlines", None)
    if inlines is not None:
        return cast(tuple[Inline, ...], inlines)
    caption = getattr(block, "caption", None)
    if caption is not None:
        return cast(tuple[Inline, ...], caption)
    return ()


def _check_internal_links_in_inline(
    inline: Inline, article: Article, diagnostics: list[Diagnostic]
) -> None:
    if isinstance(inline, InternalLinkInline):
        has_page_id = inline.target_page_id is not None
        if inline.resolution == "resolved" and not has_page_id:
            diagnostics.append(
                _make_diagnostic(
                    code="MODEL_LINK_RESOLVED_WITHOUT_PAGE_ID",
                    article=article,
                    message=(
                        f"internal link to {inline.target_title!r} is resolved "
                        "but has no target_page_id"
                    ),
                    details={"target_title": inline.target_title},
                )
            )
        elif inline.resolution in ("missing", "externalized") and has_page_id:
            diagnostics.append(
                _make_diagnostic(
                    code="MODEL_LINK_UNRESOLVED_WITH_PAGE_ID",
                    article=article,
                    message=(
                        f"internal link to {inline.target_title!r} is {inline.resolution} "
                        "but has a target_page_id"
                    ),
                    details={
                        "target_title": inline.target_title,
                        "resolution": inline.resolution,
                        "target_page_id": inline.target_page_id,
                    },
                )
            )
        for label_inline in inline.label:
            _check_internal_links_in_inline(label_inline, article, diagnostics)
        return

    for nested in _inline_children(inline):
        _check_internal_links_in_inline(nested, article, diagnostics)


def _inline_children(inline: Inline) -> tuple[Inline, ...]:
    inlines = getattr(inline, "inlines", None)
    if inlines is not None:
        return cast(tuple[Inline, ...], inlines)
    label = getattr(inline, "label", None)
    if label is not None:
        return cast(tuple[Inline, ...], label)
    return ()


def _check_diagnostic_consistency(
    embedded: Diagnostic, article: Article, diagnostics: list[Diagnostic]
) -> None:
    if embedded.page_id is not None and embedded.page_id != article.page_id:
        diagnostics.append(
            _make_diagnostic(
                code="MODEL_DIAGNOSTIC_PAGE_ID_MISMATCH",
                article=article,
                message=(
                    f"embedded diagnostic {embedded.code!r} references page_id "
                    f"{embedded.page_id}, article is {article.page_id}"
                ),
                details={"embedded_page_id": embedded.page_id, "embedded_code": embedded.code},
            )
        )
    if embedded.title is not None and embedded.title != article.title:
        diagnostics.append(
            _make_diagnostic(
                code="MODEL_DIAGNOSTIC_TITLE_MISMATCH",
                article=article,
                message=(
                    f"embedded diagnostic {embedded.code!r} references title "
                    f"{embedded.title!r}, article is {article.title!r}"
                ),
                details={"embedded_title": embedded.title, "embedded_code": embedded.code},
            )
        )


def _make_diagnostic(
    *, code: str, article: Article, message: str, details: dict[str, object]
) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity="error",
        stage="model_validate",
        page_id=article.page_id,
        title=article.title,
        message=message,
        source_path=None,
        source_excerpt=None,
        details=details,
    )
