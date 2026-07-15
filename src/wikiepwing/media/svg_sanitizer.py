"""SVG sanitizer (TASK-O006, ARCHITECTURE.md 15.4 "SVG sanitize"/"external entity禁止").

SVG is XML, so it carries XML's own threat model rather than the raw
byte-format concerns TASK-O005 handles: a `<!DOCTYPE ...>` with a custom
`<!ENTITY ...>` can drive XXE (reading local files via an external
entity) or a billion-laughs-style entity-expansion denial of service.
Rather than trying to selectively strip a DOCTYPE (fragile against
obfuscation), this module fails closed: any DOCTYPE or ENTITY
declaration anywhere in the raw bytes rejects the file outright, before
it is ever handed to `xml.etree.ElementTree`'s expat-based parser.

Once parsed, `<script>` and `<foreignObject>` elements (the two
straightforward script-execution vectors in SVG), any `on*` event
handler attribute (`onload`, `onclick`, ...), and any `href`/
`xlink:href` attribute using a `javascript:` URI are stripped from the
tree before it is re-serialized.

No new dependency: this is implemented entirely with the standard
library rather than adding `defusedxml` or similar.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import Element, ParseError

_DOCTYPE_OR_ENTITY = re.compile(rb"<!(DOCTYPE|ENTITY)\b", re.IGNORECASE)
_DANGEROUS_TAGS = frozenset({"script", "foreignObject"})
_JAVASCRIPT_URI = re.compile(r"^\s*javascript:", re.IGNORECASE)
_HREF_ATTRS = frozenset({"href", "{http://www.w3.org/1999/xlink}href"})

# Without this, ElementTree.tostring re-serializes the SVG/xlink namespaces
# as auto-generated "ns0:"/"ns1:" prefixes instead of the conventional
# xmlns="..."/xmlns:xlink="..." form real SVG consumers expect.
ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
ElementTree.register_namespace("xlink", "http://www.w3.org/1999/xlink")


class SvgSanitizeError(ValueError):
    """Raised when SVG content cannot be sanitized safely."""


def sanitize_svg(content: bytes) -> bytes:
    """Return `content` with XXE vectors, scripts, and event handlers removed."""
    if _DOCTYPE_OR_ENTITY.search(content):
        raise SvgSanitizeError("SVG must not contain a DOCTYPE or ENTITY declaration")

    try:
        root = ElementTree.fromstring(content)
    except ParseError as error:
        raise SvgSanitizeError(f"cannot parse SVG content: {error}") from error

    if _local_name(root.tag) in _DANGEROUS_TAGS:
        raise SvgSanitizeError(f"SVG root element is not allowed: <{root.tag}>")

    _sanitize_element(root)
    return ElementTree.tostring(root)


def _sanitize_element(root: Element) -> None:
    # Collect removals before mutating: ElementTree.iter() walks the live tree,
    # and removing a node while that same walk is in progress is unsafe.
    to_remove: list[tuple[Element, Element]] = []
    for parent in root.iter():
        for child in list(parent):
            if _local_name(child.tag) in _DANGEROUS_TAGS:
                to_remove.append((parent, child))
    for parent, child in to_remove:
        parent.remove(child)

    for element in root.iter():
        _strip_dangerous_attributes(element)


def _strip_dangerous_attributes(element: Element) -> None:
    for name, value in list(element.attrib.items()):
        local_name = _local_name(name)
        if local_name.lower().startswith("on"):
            del element.attrib[name]
        elif name in _HREF_ATTRS and _JAVASCRIPT_URI.match(value):
            del element.attrib[name]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag
