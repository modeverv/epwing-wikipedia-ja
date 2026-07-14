"""Root content selection (TASK-G002, ARCHITECTURE.md 12.2 pass N10).

Selects the container whose children are the article's actual content,
distinct from stripping unwanted nodes within it (TASK-G003). Wikimedia
Enterprise/MediaWiki rendered HTML conventionally wraps the article body in
`<div class="mw-parser-output">`; this is a documented assumption (no
concrete selector is specified in ARCHITECTURE.md/DATA_CONTRACTS.md), since
no real sample HTML with this wrapper exists in the repository's fixtures.
"""

from __future__ import annotations

from collections.abc import Callable

from wikiepwing.normalize.html_parser import ElementNode, Node

_PARSER_OUTPUT_CLASS = "mw-parser-output"


def select_root_content(document: ElementNode) -> tuple[Node, ...]:
    """Return the children of the article's content root within a parsed document."""
    parser_output = _find_first(document, lambda node: _has_class(node, _PARSER_OUTPUT_CLASS))
    if parser_output is not None:
        return parser_output.children

    body = _find_first(document, lambda node: node.tag == "body")
    if body is not None:
        return body.children

    return document.children


def _has_class(node: ElementNode, class_name: str) -> bool:
    if node.tag != "div":
        return False
    for name, value in node.attributes:
        if name == "class":
            return class_name in value.split()
    return False


def _find_first(node: ElementNode, predicate: Callable[[ElementNode], bool]) -> ElementNode | None:
    if predicate(node):
        return node
    for child in node.children:
        if isinstance(child, ElementNode):
            found = _find_first(child, predicate)
            if found is not None:
                return found
    return None
