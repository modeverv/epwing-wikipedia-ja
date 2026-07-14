"""Heading conversion (TASK-G004, ARCHITECTURE.md 12.2 pass N30).

Converts `<h1>`-`<h6>` elements into `HeadingBlock`. Anchor extraction follows
MediaWiki's conventional patterns (own `id` attribute, or a nested element's
`id` such as the historical `<span class="mw-headline" id="...">` wrapper) as
a documented assumption, since ARCHITECTURE.md does not specify a concrete
algorithm. Heading text is flattened into a single TextInline rather than
richly converted, since this task depends only on TASK-G003 and not on the
paragraph/inline conversion machinery built in TASK-G005/G006.
"""

from __future__ import annotations

from wikiepwing.model.blocks import HeadingBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import Inline, TextInline
from wikiepwing.normalize.html_parser import ElementNode, Node, TextNode

_HEADING_LEVELS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
_FALLBACK_ANCHOR = "section"


def is_heading(node: Node) -> bool:
    """Return whether `node` is an `<h1>`-`<h6>` element."""
    return isinstance(node, ElementNode) and node.tag in _HEADING_LEVELS


def convert_heading(node: ElementNode) -> tuple[HeadingBlock, tuple[Diagnostic, ...]]:
    """Convert one heading element into a HeadingBlock, plus any diagnostics."""
    if node.tag not in _HEADING_LEVELS:
        raise ValueError(f"not a heading element: <{node.tag}>")

    diagnostics: list[Diagnostic] = []
    text = _flatten_text(node)
    anchor = _find_id(node) or _slugify(text)
    if not anchor:
        anchor = _FALLBACK_ANCHOR
        diagnostics.append(_make_diagnostic("DOM_HEADING_ANCHOR_FALLBACK", node))
    if not text:
        diagnostics.append(_make_diagnostic("DOM_EMPTY_HEADING", node))

    inlines: tuple[Inline, ...] = (TextInline(value=text),) if text else ()
    heading = HeadingBlock(level=_HEADING_LEVELS[node.tag], anchor=anchor, inlines=inlines)
    return heading, tuple(diagnostics)


def _find_id(node: ElementNode) -> str | None:
    for name, value in node.attributes:
        if name == "id" and value:
            return value
    for child in node.children:
        if isinstance(child, ElementNode):
            found = _find_id(child)
            if found is not None:
                return found
    return None


def _flatten_text(node: ElementNode) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, TextNode):
            parts.append(child.text)
        elif isinstance(child, ElementNode):
            parts.append(_flatten_text(child))
    return "".join(parts).strip()


def _slugify(text: str) -> str:
    return "_".join(text.split())


def _make_diagnostic(code: str, node: ElementNode) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity="warning",
        stage="normalize_headings",
        page_id=None,
        title=None,
        message=f"<{node.tag}> heading required a fallback",
        source_path=None,
        source_excerpt=None,
        details={},
    )
