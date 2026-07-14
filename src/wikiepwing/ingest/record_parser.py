"""Parse one Wikimedia Enterprise NDJSON record into a typed RawArticle."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import cast


class RecordParseError(ValueError):
    """Raised when an NDJSON record cannot be parsed into a RawArticle."""


@dataclass(frozen=True, slots=True)
class LicenseRecord:
    """One license entry attached to an article."""

    identifier: str
    name: str
    url: str


@dataclass(frozen=True, slots=True)
class SourceImage:
    """The article's main image, as declared by the source record."""

    content_url: str
    width: int | None
    height: int | None


@dataclass(frozen=True, slots=True)
class RawArticle:
    """One article as extracted from a Wikimedia Enterprise NDJSON record."""

    page_id: int
    revision_id: int
    title: str
    namespace_id: int
    url: str
    date_modified: datetime
    html: str | None
    wikitext: str | None
    redirects: tuple[str, ...]
    categories: tuple[str, ...]
    templates: tuple[str, ...]
    licenses: tuple[LicenseRecord, ...]
    main_image: SourceImage | None
    source_sequence: int
    source_hash: str


def parse_record(line: bytes, *, source_sequence: int) -> RawArticle:
    """Parse one raw NDJSON line into a RawArticle, hashing the line as source_hash."""
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as error:
        raise RecordParseError(
            f"record at source_sequence {source_sequence} is not valid JSON: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise RecordParseError(f"record at source_sequence {source_sequence} must be a JSON object")
    fields = cast(dict[str, object], payload)

    page_id = _require_int(fields, "identifier", source_sequence, "identifier")
    version = _require_object(fields, "version", source_sequence, "version")
    revision_id = _require_int(version, "identifier", source_sequence, "version.identifier")
    title = _require_string(fields, "name", source_sequence, "name")
    namespace = _require_object(fields, "namespace", source_sequence, "namespace")
    namespace_id = _require_int(namespace, "identifier", source_sequence, "namespace.identifier")
    url = _require_string(fields, "url", source_sequence, "url")
    date_modified = _require_datetime(fields, "date_modified", source_sequence)

    article_body = fields.get("article_body")
    if not isinstance(article_body, dict):
        raise RecordParseError(
            f"record at source_sequence {source_sequence} is missing article_body"
        )
    body = cast(dict[str, object], article_body)
    html = _optional_string(body, "html")
    wikitext = _optional_string(body, "wikitext")

    redirects = _optional_named_list(fields, "redirects", source_sequence)
    categories = _optional_named_list(fields, "categories", source_sequence)
    templates = _optional_named_list(fields, "templates", source_sequence)
    licenses = _parse_licenses(fields, source_sequence)
    main_image = _parse_main_image(fields)

    return RawArticle(
        page_id=page_id,
        revision_id=revision_id,
        title=title,
        namespace_id=namespace_id,
        url=url,
        date_modified=date_modified,
        html=html,
        wikitext=wikitext,
        redirects=redirects,
        categories=categories,
        templates=templates,
        licenses=licenses,
        main_image=main_image,
        source_sequence=source_sequence,
        source_hash=hashlib.sha256(line).hexdigest(),
    )


def _require_object(
    fields: dict[str, object], key: str, source_sequence: int, path: str
) -> dict[str, object]:
    value = fields.get(key)
    if not isinstance(value, dict):
        raise RecordParseError(
            f"record at source_sequence {source_sequence} is missing object field: {path}"
        )
    return cast(dict[str, object], value)


def _require_string(fields: dict[str, object], key: str, source_sequence: int, path: str) -> str:
    value = fields.get(key)
    if not isinstance(value, str) or not value:
        raise RecordParseError(
            f"record at source_sequence {source_sequence} "
            f"is missing a non-empty string field: {path}"
        )
    return value


def _require_int(fields: dict[str, object], key: str, source_sequence: int, path: str) -> int:
    value = fields.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise RecordParseError(
            f"record at source_sequence {source_sequence} is missing an integer field: {path}"
        )
    return value


def _require_datetime(fields: dict[str, object], key: str, source_sequence: int) -> datetime:
    value = fields.get(key)
    if not isinstance(value, str):
        raise RecordParseError(
            f"record at source_sequence {source_sequence} is missing string field: {key}"
        )
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise RecordParseError(
            f"record at source_sequence {source_sequence} has an invalid {key}: {error}"
        ) from error


def _optional_string(fields: dict[str, object], key: str) -> str | None:
    value = fields.get(key)
    return value if isinstance(value, str) and value else None


def _optional_named_list(
    fields: dict[str, object], key: str, source_sequence: int
) -> tuple[str, ...]:
    value = fields.get(key)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise RecordParseError(
            f"record at source_sequence {source_sequence} field {key} must be a JSON array"
        )
    names: list[str] = []
    for index, item in enumerate(cast(list[object], value)):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
            raise RecordParseError(
                f"record at source_sequence {source_sequence} {key}[{index}] "
                "is missing a non-empty string name"
            )
        names.append(cast(str, item["name"]))
    return tuple(names)


def _parse_licenses(fields: dict[str, object], source_sequence: int) -> tuple[LicenseRecord, ...]:
    value = fields.get("license")
    if value is None:
        return ()
    if not isinstance(value, list):
        raise RecordParseError(
            f"record at source_sequence {source_sequence} field license must be a JSON array"
        )
    licenses: list[LicenseRecord] = []
    for index, item in enumerate(cast(list[object], value)):
        if not isinstance(item, dict):
            raise RecordParseError(
                f"record at source_sequence {source_sequence} "
                f"license[{index}] must be a JSON object"
            )
        entry = cast(dict[str, object], item)
        identifier = entry.get("identifier")
        name = entry.get("name")
        url = entry.get("url")
        if not all(isinstance(value, str) and value for value in (identifier, name, url)):
            raise RecordParseError(
                f"record at source_sequence {source_sequence} license[{index}] "
                "is missing identifier/name/url"
            )
        licenses.append(
            LicenseRecord(
                identifier=cast(str, identifier), name=cast(str, name), url=cast(str, url)
            )
        )
    return tuple(licenses)


def _parse_main_image(fields: dict[str, object]) -> SourceImage | None:
    value = fields.get("image")
    if not isinstance(value, dict):
        return None
    image = cast(dict[str, object], value)
    content_url = image.get("content_url")
    if not isinstance(content_url, str) or not content_url:
        content_url_candidate = image.get("url")
        content_url = content_url_candidate if isinstance(content_url_candidate, str) else None
    if not content_url:
        return None
    width = image.get("width")
    height = image.get("height")
    return SourceImage(
        content_url=content_url,
        width=width if isinstance(width, int) and not isinstance(width, bool) else None,
        height=height if isinstance(height, int) and not isinstance(height, bool) else None,
    )
