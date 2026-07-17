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
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from functools import cache

from wikiepwing.gaiji.classifier import classify_character
from wikiepwing.gaiji.code_assignment import MAX_GAIJI_PER_WIDTH, assign_gaiji_codes
from wikiepwing.gaiji.substitutions import (
    DEFAULT_SUBSTITUTIONS,
    normalize_with_safe_substitutions,
)
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
    body_replacements: dict[int, str] = field(default_factory=dict)
    fallback_characters: frozenset[str] = frozenset()

    def is_empty(self) -> bool:
        """Return whether this plan has no gaiji candidates at all."""
        return not self.assigned_codes


@cache
def _classify(character: str) -> str:
    # Full-corpus bodies contain billions of repeated characters. The
    # classification depends only on one Unicode scalar and the immutable
    # default substitution table, so caching avoids repeating the same
    # codec/category work for every occurrence.
    return classify_character(character, substitutions=DEFAULT_SUBSTITUTIONS)


def plan_gaiji_codes(
    texts: Iterable[str],
    *,
    on_progress: Callable[[int, int], None] | None = None,
    total: int | None = None,
    max_per_width: int = MAX_GAIJI_PER_WIDTH,
) -> GaijiPlan:
    """Scan every string in `texts`, assigning deterministic gaiji codes to distinct candidates.

    `texts` should cover every body string that will call `embed_gaiji_tokens`
    (title/alias text never produces gaiji candidates -- see module docstring
    -- so it need not be included here, though including it is harmless).
    """
    all_character_counts: Counter[str] = Counter()
    for index, text in enumerate(texts, start=1):
        # Counter's string fast path counts occurrences in C. Classifying the
        # small corpus-wide distinct set afterwards avoids a Python callback
        # for every character in a multi-gigabyte Wikipedia body stream.
        all_character_counts.update(normalize_with_safe_substitutions(text))
        if on_progress is not None:
            on_progress(index, total if total is not None else index)

    usage_counts: Counter[str] = Counter(
        {
            character: count
            for character, count in all_character_counts.items()
            if _classify(character) == "C"
        }
    )

    width_classes = {character: gaiji_width_class(character) for character in usage_counts}
    candidates_by_width: dict[str, list[str]] = {"narrow": [], "wide": []}
    for character, width_class in width_classes.items():
        candidates_by_width[width_class].append(character)

    # FreePWING has independent 8,192-character narrow/wide code spaces. Keep
    # the most frequently used glyphs so a full-corpus build preserves the
    # greatest number of occurrences; Unicode order breaks equal-count ties,
    # making both selection and subsequent code assignment deterministic.
    selected: list[str] = []
    for candidates in candidates_by_width.values():
        selected.extend(
            sorted(candidates, key=lambda character: (-usage_counts[character], character))[
                :max_per_width
            ]
        )
    assigned = assign_gaiji_codes(
        ((character, width_classes[character]) for character in selected),
        max_per_width=max_per_width,
    )
    body_replacements: dict[int, str] = {}
    fallback_characters: set[str] = set()
    for character in all_character_counts:
        classification = _classify(character)
        if classification == "A":
            continue
        if classification == "C" and character in assigned:
            replacement = GAIJI_TOKEN_FORMAT.format(code=assigned[character])
        else:
            replacement = unrepresentable_fallback(character)
            fallback_characters.add(character)
        body_replacements[ord(character)] = replacement
    return GaijiPlan(
        assigned_codes=assigned,
        width_classes=width_classes,
        usage_counts=dict(usage_counts),
        body_replacements=body_replacements,
        fallback_characters=frozenset(fallback_characters),
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
    normalized = normalize_with_safe_substitutions(text)
    replacements = plan.body_replacements
    fallback_characters = plan.fallback_characters
    if not replacements:
        replacements, fallback_characters = _build_body_replacements(set(normalized), plan)
    if tracker is not None and fallback_characters:
        counts = Counter(normalized)
        for character in counts.keys() & fallback_characters:
            tracker.record_many(character, counts[character], page_id=page_id, title=title)
    return normalized.translate(replacements)


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
    normalized = normalize_with_safe_substitutions(text)
    counts = Counter(normalized)
    replacements = {
        ord(character): unrepresentable_fallback(character)
        for character in counts
        if _classify(character) != "A"
    }
    if tracker is not None:
        for character, count in counts.items():
            if ord(character) in replacements:
                tracker.record_many(character, count, page_id=page_id, title=title)
    return normalized.translate(replacements)


def _build_body_replacements(
    characters: set[str], plan: GaijiPlan
) -> tuple[dict[int, str], frozenset[str]]:
    replacements: dict[int, str] = {}
    fallback_characters: set[str] = set()
    for character in characters:
        classification = _classify(character)
        if classification == "A":
            continue
        if classification == "C" and character in plan.assigned_codes:
            replacement = GAIJI_TOKEN_FORMAT.format(code=plan.assigned_codes[character])
        else:
            replacement = unrepresentable_fallback(character)
            fallback_characters.add(character)
        replacements[ord(character)] = replacement
    return replacements, frozenset(fallback_characters)
