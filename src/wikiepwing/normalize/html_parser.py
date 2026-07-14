"""Safe HTML parsing into a minimal DOM tree (TASK-G001).

Built on `html.parser.HTMLParser`, which performs no network I/O and resolves
entities/character references purely from Python's built-in tables (no
external DTD fetch, no XXE-style risk). This module only builds a tree and
recovers from malformed structure; root content selection (TASK-G002),
unsafe/UI node removal (TASK-G003), and conversion to Block/Inline (TASK-G004
onward) are separate tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser as _StdlibHTMLParser

from wikiepwing.model.diagnostics import Diagnostic

_VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)

_ROOT_TAG = "#document"


class HtmlParseError(ValueError):
    """Raised when HTML cannot be parsed (or, with recovery disabled, when it is malformed)."""


@dataclass(frozen=True, slots=True)
class TextNode:
    """A run of text content."""

    text: str


@dataclass(frozen=True, slots=True)
class ElementNode:
    """One HTML element and its children."""

    tag: str
    attributes: tuple[tuple[str, str], ...]
    children: tuple[Node, ...]


Node = ElementNode | TextNode


@dataclass(frozen=True, slots=True)
class HtmlParseResult:
    """The parsed DOM tree plus any recovery diagnostics."""

    root: ElementNode
    diagnostics: tuple[Diagnostic, ...]


class _PendingElement:
    """A still-open element on the parser's stack. `children` is `None` once excluded by depth."""

    __slots__ = ("tag", "attributes", "children")

    def __init__(self, tag: str, attributes: tuple[tuple[str, str], ...], included: bool) -> None:
        self.tag = tag
        self.attributes = attributes
        self.children: list[Node] | None = [] if included else None


def parse_html(html: str, *, max_dom_depth: int, html_recover: bool = True) -> HtmlParseResult:
    """Parse `html` into a minimal DOM tree, recovering from malformed structure."""
    if max_dom_depth < 1:
        raise HtmlParseError("max_dom_depth must be positive")
    builder = _TreeBuilder(max_dom_depth=max_dom_depth, html_recover=html_recover)
    builder.feed(html)
    return builder.finalize_result()


class _TreeBuilder(_StdlibHTMLParser):
    def __init__(self, *, max_dom_depth: int, html_recover: bool) -> None:
        super().__init__(convert_charrefs=True)
        self._max_dom_depth = max_dom_depth
        self._html_recover = html_recover
        self._diagnostics: list[Diagnostic] = []
        self._stack: list[_PendingElement] = [_PendingElement(_ROOT_TAG, (), included=True)]

    def finalize_result(self) -> HtmlParseResult:
        self.close()
        while len(self._stack) > 1:
            pending = self._stack.pop()
            self._report(
                "DOM_UNCLOSED_TAG", f"unclosed element at end of document: <{pending.tag}>"
            )
            self._attach_to_parent(pending)
        root_children = self._stack[0].children or []
        return HtmlParseResult(
            root=ElementNode(tag=_ROOT_TAG, attributes=(), children=tuple(root_children)),
            diagnostics=tuple(self._diagnostics),
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start_element(tag, attrs, self_closing=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start_element(tag, attrs, self_closing=True)

    def _start_element(
        self, tag: str, attrs: list[tuple[str, str | None]], *, self_closing: bool
    ) -> None:
        depth = len(self._stack)
        included = depth <= self._max_dom_depth
        if not included and depth == self._max_dom_depth + 1:
            self._report(
                "DOM_MAX_DEPTH_EXCEEDED",
                f"element <{tag}> exceeded max_dom_depth {self._max_dom_depth}",
            )
        attributes = tuple((name, value or "") for name, value in attrs)
        pending = _PendingElement(tag, attributes, included=included)
        if tag in _VOID_ELEMENTS or self_closing:
            self._attach_to_parent(pending)
            return
        self._stack.append(pending)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_ELEMENTS:
            return
        match_index = None
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                match_index = index
                break
        if match_index is None:
            self._report("DOM_UNMATCHED_END_TAG", f"unmatched closing tag: </{tag}>")
            return
        while len(self._stack) - 1 > match_index:
            pending = self._stack.pop()
            self._report("DOM_UNCLOSED_TAG", f"unclosed element: <{pending.tag}>")
            self._attach_to_parent(pending)
        self._attach_to_parent(self._stack.pop())

    def handle_data(self, data: str) -> None:
        if not data:
            return
        current = self._stack[-1]
        if current.children is not None:
            current.children.append(TextNode(text=data))

    def handle_comment(self, data: str) -> None:
        return

    def handle_decl(self, decl: str) -> None:
        return

    def handle_pi(self, data: str) -> None:
        return

    def _attach_to_parent(self, pending: _PendingElement) -> None:
        if pending.children is None:
            return
        parent = self._stack[-1]
        if parent.children is not None:
            parent.children.append(
                ElementNode(
                    tag=pending.tag, attributes=pending.attributes, children=tuple(pending.children)
                )
            )

    def _report(self, code: str, message: str) -> None:
        if not self._html_recover:
            raise HtmlParseError(message)
        self._diagnostics.append(
            Diagnostic(
                code=code,
                severity="warning",
                stage="normalize_html_parse",
                page_id=None,
                title=None,
                message=message,
                source_path=None,
                source_excerpt=None,
                details={},
            )
        )
