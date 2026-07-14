"""Infobox detector (TASK-K007, ARCHITECTURE.md 11.6).

`InfoboxBlock` is not a `TableBlock` alias -- it is the article-lead
metadata box MediaWiki's `Template:Infobox` renders as `<table class="
infobox ...">` (subtype templates add further classes, e.g. "vcard" or a
biography-specific class, but always keep the base "infobox" token). This
module relies on that one stable, project-wide convention rather than
enumerating specific infobox template classes.
"""

from __future__ import annotations

from wikiepwing.normalize.html_parser import ElementNode, Node, has_class
from wikiepwing.normalize.tables import is_table

_INFOBOX_CLASS = "infobox"


def is_infobox(node: Node) -> bool:
    """Return whether `node` is a `<table>` element carrying the "infobox" class."""
    if not is_table(node):
        return False
    assert isinstance(node, ElementNode)
    return has_class(node, _INFOBOX_CLASS)
