"""Gaiji detection, code planning, and text embedding (GAIJI.md, ARCHITECTURE.md 18).

Wires TASK-M001-M009's gaiji library modules end to end for the one place
they were never connected to (GAIJI.md sections 1-2): every string that will
reach FreePWING's EUC-JP-only `FPWParser` (title, aliases, body) needs its
category B/C/D characters (18.1) resolved before it gets there.

`plan_gaiji_codes` must see every candidate character from the whole corpus
before it can assign codes deterministically (TASK-M006, DATA_CONTRACTS.md
10 forbids processing-order dependence), so callers always run it once over
every entry's text, then call `embed_gaiji_tokens`/`embed_title_fallback` per
field using the resulting plan -- never the other way around.

Body text gets full A/C/D handling: category C characters become a
`@@GAIJI:<assigned_code>@@` placeholder token that
`docker/toolchain/freepwing_build_entries.pl` turns into an
`add_half_user_character`/`add_full_user_character` call (the same
placeholder-token design `v1/toolchain/records/build_records.pl` used
successfully before this project's split/rewrite). Title and alias text
never gets gaiji tokens, even for category C characters: those strings are
also used verbatim as search index keys
(`wikiepwing.render.freepwing_source`'s `word2->add_entry` headword), and a
literal `@@GAIJI:...@@` token in a headword would make that entry
unfindable by normal search input. So title/alias text collapses category
C the same way as category D: 18.5's `[U+XXXX]` codepoint fallback.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from wikiepwing.gaiji.classifier import classify_character
from wikiepwing.gaiji.code_assignment import assign_gaiji_codes
from wikiepwing.gaiji.substitutions import DEFAULT_SUBSTITUTIONS, apply_safe_substitutions
from wikiepwing.gaiji.unrepresentable import UnrepresentableTracker, unrepresentable_fallback

GAIJI_TOKEN_FORMAT = "@@GAIJI:{code}@@"


def gaiji_width_class(character: str) -> str:
    """Classify `character` into FreePWING's narrow or wide gaiji code space.

    East Asian Wide/Fullwidth characters (Unicode's `east_asian_width`
    property) go in the wide (`FullUserChar`) space; everything else
    (Narrow, Halfwidth, Ambiguous, Neutral) goes in the narrow
    (`HalfUserChar`) space, matching `tests/fixtures/handcrafted/build_fixture.pl`'s
    `add_half_user_character`/`add_full_user_character` split.
    """
    return "wide" if unicodedata.east_asian_width(character) in ("W", "F") else "narrow"


@dataclass(frozen=True, slots=True)
class GaijiPlan:
    """Deterministic `assigned_code` per distinct gaiji candidate character (TASK-M006)."""

    assigned_codes: dict[str, str]
    width_classes: dict[str, str]
    usage_counts: dict[str, int]

    def is_empty(self) -> bool:
        """Return whether this plan has no gaiji candidates at all."""
        return not self.assigned_codes


def _classify(character: str) -> str:
    return classify_character(character, substitutions=DEFAULT_SUBSTITUTIONS)


def _candidate_characters(text: str) -> Iterator[str]:
    normalized, _diagnostics = apply_safe_substitutions(text)
    for character in normalized:
        if _classify(character) == "C":
            yield character


def plan_gaiji_codes(texts: Iterable[str]) -> GaijiPlan:
    """Scan every string in `texts`, assigning deterministic gaiji codes to distinct candidates.

    `texts` should cover every body string that will call `embed_gaiji_tokens`
    (title/alias text never produces gaiji candidates -- see module docstring
    -- so it need not be included here, though including it is harmless).
    """
    usage_counts: Counter[str] = Counter()
    for text in texts:
        usage_counts.update(_candidate_characters(text))

    width_classes = {character: gaiji_width_class(character) for character in usage_counts}
    assigned = assign_gaiji_codes(
        (character, width_classes[character]) for character in sorted(usage_counts)
    )
    return GaijiPlan(
        assigned_codes=assigned, width_classes=width_classes, usage_counts=dict(usage_counts)
    )


def embed_gaiji_tokens(
    text: str,
    *,
    plan: GaijiPlan,
    tracker: UnrepresentableTracker | None = None,
    page_id: int | None = None,
    title: str | None = None,
) -> str:
    """Rewrite `text` (body text), replacing category C/D characters per `plan` and 18.5."""
    normalized, _diagnostics = apply_safe_substitutions(text)
    pieces: list[str] = []
    for character in normalized:
        classification = _classify(character)
        if classification == "A":
            pieces.append(character)
        elif classification == "C" and character in plan.assigned_codes:
            pieces.append(GAIJI_TOKEN_FORMAT.format(code=plan.assigned_codes[character]))
        else:
            pieces.append(unrepresentable_fallback(character))
            if tracker is not None:
                tracker.record(character, page_id=page_id, title=title)
    return "".join(pieces)


def embed_title_fallback(
    text: str,
    *,
    tracker: UnrepresentableTracker | None = None,
    page_id: int | None = None,
    title: str | None = None,
) -> str:
    """Rewrite `text` (title/alias/headword text): category A unchanged, everything else bracketed.

    Title and alias strings are also used as literal search index keys, so
    they never carry a gaiji placeholder token -- see module docstring.
    """
    normalized, _diagnostics = apply_safe_substitutions(text)
    pieces: list[str] = []
    for character in normalized:
        if _classify(character) == "A":
            pieces.append(character)
        else:
            pieces.append(unrepresentable_fallback(character))
            if tracker is not None:
                tracker.record(character, page_id=page_id, title=title)
    return "".join(pieces)
