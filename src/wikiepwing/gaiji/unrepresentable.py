"""Unrepresentable (category D) character fallback and tracking (TASK-M008, ARCHITECTURE.md 18.5).

18.5: a category-D character (TASK-M002) is never dropped down to a bare
replacement marker -- it falls back to its codepoint notation
(`"[U+1F600]"`), and the build tracks how often each one occurs, in what
rank order, and in which articles, for TASK-M009's report to consume.
Example articles per character are capped (`DATA_CONTRACTS.md` 11's
"details_json"/excerpt size-limiting precedent) so a heavily affected
build can't grow this tracker's memory use without bound; the occurrence
*count* itself is never capped.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

DEFAULT_MAX_EXAMPLES_PER_CHARACTER = 5


def unrepresentable_fallback(character: str) -> str:
    """Return `character`'s ARCHITECTURE.md 18.5 codepoint-notation fallback."""
    return f"[U+{ord(character):04X}]"


@dataclass(frozen=True, slots=True)
class UnrepresentableExample:
    """One article where an unrepresentable character was found."""

    page_id: int | None
    title: str | None


@dataclass(frozen=True, slots=True)
class UnrepresentableStat:
    """One character's aggregated occurrence statistics."""

    character: str
    count: int
    examples: tuple[UnrepresentableExample, ...]


@dataclass(slots=True)
class _CharacterRecord:
    count: int = 0
    examples: list[UnrepresentableExample] = field(default_factory=list)


class UnrepresentableTracker:
    """Aggregates category-D character occurrences across a build."""

    def __init__(self, *, max_examples_per_character: int = DEFAULT_MAX_EXAMPLES_PER_CHARACTER):
        if max_examples_per_character < 0:
            raise ValueError("max_examples_per_character must not be negative")
        self._max_examples = max_examples_per_character
        self._records: dict[str, _CharacterRecord] = {}

    def record(
        self, character: str, *, page_id: int | None = None, title: str | None = None
    ) -> None:
        """Record one occurrence of `character`, keeping only the first N examples."""
        self.record_many(character, 1, page_id=page_id, title=title)

    def record_many(
        self,
        character: str,
        count: int,
        *,
        page_id: int | None = None,
        title: str | None = None,
    ) -> None:
        """Record repeated occurrences without a Python call per occurrence."""
        if count < 0:
            raise ValueError("count must not be negative")
        if count == 0:
            return
        record = self._records.setdefault(character, _CharacterRecord())
        record.count += count
        examples_to_add = min(count, self._max_examples - len(record.examples))
        record.examples.extend(
            UnrepresentableExample(page_id=page_id, title=title) for _ in range(examples_to_add)
        )

    def most_frequent(self, limit: int | None = None) -> tuple[UnrepresentableStat, ...]:
        """Return stats ordered by count descending, ties broken by codepoint ascending."""
        stats = tuple(
            UnrepresentableStat(
                character=character, count=record.count, examples=tuple(record.examples)
            )
            for character, record in self._records.items()
        )
        ordered = tuple(sorted(stats, key=lambda stat: (-stat.count, stat.character)))
        return ordered if limit is None else ordered[:limit]

    def total_occurrences(self) -> int:
        """Return the total occurrence count across every tracked character."""
        return sum(record.count for record in self._records.values())

    def characters(self) -> Iterable[str]:
        """Return every distinct character tracked so far."""
        return tuple(self._records.keys())
