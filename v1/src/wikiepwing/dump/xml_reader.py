"""Bounded-memory MediaWiki XML ingestion."""

from __future__ import annotations

import bz2
import re
import xml.etree.ElementTree as element_tree
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from wikiepwing.storage.database import RawPage

REDIRECT = re.compile(r"^\s*#redirect\s*\[\[([^\]|#]+)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class IngestionStats:
    pages_seen: int
    pages_kept: int


def stream_pages(path: Path, namespaces: set[int] | None = None) -> Iterator[RawPage]:
    """Yield main records with `iterparse`, clearing processed page elements."""
    try:
        included_namespaces = {0} if namespaces is None else namespaces
        source = bz2.open(path, "rb") if path.suffix == ".bz2" else path.open("rb")
        context = element_tree.iterparse(source, events=("end",))
        for _, element in context:
            if element.tag.rsplit("}", 1)[-1] != "page":
                continue
            fields = {child.tag.rsplit("}", 1)[-1]: child for child in element}
            namespace = int(fields.get("ns", element_tree.Element("ns")).text or "0")
            if namespace in included_namespaces:
                revision = fields.get("revision")
                revision_fields = (
                    {}
                    if revision is None
                    else {child.tag.rsplit("}", 1)[-1]: child for child in revision}
                )
                text = revision_fields.get("text", element_tree.Element("text")).text or ""
                redirect = fields.get("redirect")
                redirect_target = redirect.get("title") if redirect is not None else None
                if redirect_target is None:
                    match = REDIRECT.match(text)
                    redirect_target = match.group(1).strip() if match else None
                yield RawPage(
                    int(fields["id"].text or "0"),
                    fields["title"].text or "",
                    namespace,
                    int(revision_fields["id"].text)
                    if revision_fields.get("id") is not None and revision_fields["id"].text
                    else None,
                    text,
                    redirect_target,
                )
            element.clear()
        source.close()
    except element_tree.ParseError as error:
        raise ValueError(f"malformed MediaWiki XML: {error}") from error
