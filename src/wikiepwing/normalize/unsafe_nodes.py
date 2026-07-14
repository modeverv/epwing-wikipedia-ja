"""Unsafe/UI node removal (TASK-G003, ARCHITECTURE.md 12.2 pass N20).

`script`/`style` elements are always removed as an unconditional safety
measure (ARCHITECTURE.md 12.1: "script/style/template-like executable
contentを除去する"). The remaining ARCHITECTURE.md 12.3 exclusion
candidates (edit links, navboxes, authority control boxes) are removed only
when their corresponding `[normalize]` config flag is enabled, since those
are the only three categories with an existing config flag and a concrete
selector (`.mw-editsection`, given in 12.4's example). The other 12.3
candidates (coordinates UI duplication, hidden metadata, maintenance
category display, portal box, language switch UI) are deliberately left
unimplemented: ARCHITECTURE.md 12.3 itself says classes that might drop
information should only be added "once confirmed via fixtures", and no
concrete class name for them exists in this repository yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from wikiepwing.config import AppConfig
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode, has_class

_ALWAYS_REMOVED_TAGS = frozenset({"script", "style"})


@dataclass(frozen=True, slots=True)
class UnsafeNodeRemovalOptions:
    """Which optional `[normalize]`-configured UI categories to strip."""

    remove_edit_ui: bool
    remove_navboxes: bool
    remove_authority_control: bool

    @classmethod
    def from_config(cls, config: AppConfig) -> UnsafeNodeRemovalOptions:
        """Build options from the `[normalize]` configuration section."""
        normalize = config.section("normalize")
        return cls(
            remove_edit_ui=cast(bool, normalize["remove_edit_ui"]),
            remove_navboxes=cast(bool, normalize["remove_navboxes"]),
            remove_authority_control=cast(bool, normalize["remove_authority_control"]),
        )


def remove_unsafe_nodes(
    nodes: tuple[Node, ...], options: UnsafeNodeRemovalOptions
) -> tuple[tuple[Node, ...], tuple[Diagnostic, ...]]:
    """Strip unsafe/UI nodes from `nodes`, returning the filtered tree and diagnostics."""
    diagnostics: list[Diagnostic] = []
    kept = _filter_children(nodes, options, diagnostics)
    return tuple(kept), tuple(diagnostics)


def _filter_children(
    nodes: tuple[Node, ...], options: UnsafeNodeRemovalOptions, diagnostics: list[Diagnostic]
) -> list[Node]:
    kept: list[Node] = []
    for node in nodes:
        if isinstance(node, TextNode):
            kept.append(node)
            continue
        code = _removal_code(node, options)
        if code is not None:
            diagnostics.append(_make_diagnostic(code, node))
            continue
        kept.append(
            ElementNode(
                tag=node.tag,
                attributes=node.attributes,
                children=tuple(_filter_children(node.children, options, diagnostics)),
            )
        )
    return kept


def _removal_code(node: ElementNode, options: UnsafeNodeRemovalOptions) -> str | None:
    if node.tag in _ALWAYS_REMOVED_TAGS:
        return "DOM_EXECUTABLE_CONTENT_REMOVED"
    if options.remove_edit_ui and has_class(node, "mw-editsection"):
        return "DOM_EDIT_UI_REMOVED"
    if options.remove_navboxes and has_class(node, "navbox"):
        return "DOM_NAVBOX_REMOVED"
    if options.remove_authority_control and has_class(node, "authority-control"):
        return "DOM_AUTHORITY_CONTROL_REMOVED"
    return None


def _make_diagnostic(code: str, node: ElementNode) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity="info",
        stage="normalize_unsafe_nodes",
        page_id=None,
        title=None,
        message=f"removed <{node.tag}> element",
        source_path=None,
        source_excerpt=None,
        details={},
    )
