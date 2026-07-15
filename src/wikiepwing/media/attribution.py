"""Media attribution model (TASK-O010, ARCHITECTURE.md 28.2, DATA_CONTRACTS.md image cache).

Mirrors the exact `attribution` shape of the image cache metadata JSON
in DATA_CONTRACTS.md: `source_page_url` (the Commons/File page an image
came from), `author`, `license_identifier`, and `license_url` -- every
field nullable, since 28.2 expects some of these to be genuinely
unavailable ("取得できない項目はmissingとして記録").

Actually fetching this information from a Commons/File page is a
separate feature (28.2's own wording, "別機能"); this module only
models the data and offers `is_licensed` as the one predicate every
later consumer needs (e.g. a future build-profile policy deciding
whether to keep an unlicensed image) -- that policy itself is out of
scope here, since a `build_profile` concept doesn't exist in the
codebase yet (EPIC P hasn't started).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast


class AttributionError(ValueError):
    """Raised when a MediaAttribution cannot be constructed or decoded safely."""


@dataclass(frozen=True, slots=True)
class MediaAttribution:
    """One image's attribution metadata, matching DATA_CONTRACTS.md's `attribution` shape."""

    source_page_url: str | None
    author: str | None
    license_identifier: str | None
    license_url: str | None

    def payload(self) -> dict[str, object]:
        """Return this attribution's JSON-serializable representation."""
        return {
            "source_page_url": self.source_page_url,
            "author": self.author,
            "license_identifier": self.license_identifier,
            "license_url": self.license_url,
        }


def is_licensed(attribution: MediaAttribution | None) -> bool:
    """Return whether `attribution` records a usable license identifier."""
    return attribution is not None and attribution.license_identifier is not None


def parse_media_attribution(payload: object) -> MediaAttribution:
    """Parse one JSON object into a MediaAttribution."""
    if not isinstance(payload, dict):
        raise AttributionError("attribution must be a JSON object")
    fields = cast(dict[str, object], payload)
    return MediaAttribution(
        source_page_url=_optional_str(fields, "source_page_url"),
        author=_optional_str(fields, "author"),
        license_identifier=_optional_str(fields, "license_identifier"),
        license_url=_optional_str(fields, "license_url"),
    )


def _optional_str(fields: dict[str, object], key: str) -> str | None:
    value = fields.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise AttributionError(f"attribution field {key} must be a string or null")
    return value
