"""Deterministic gaiji code assignment (TASK-M006, DATA_CONTRACTS.md 10).

DATA_CONTRACTS.md 10 requires gaiji code assignment to use "Unicode sort
order + width classなどの決定論的規則" and forbids processing-order
dependence -- the same set of registered gaiji sequences must always
produce the same `assigned_code` values, regardless of what order they
happened to be discovered in during a build.

`narrow` and `wide` gaiji live in separate EB Library code spaces (see
`tests/fixtures/handcrafted/halfchars.txt`/`fullchars.txt`, two distinct
files), so this module assigns each width class its own sequential
numbering, ordered by the sequence's own Unicode sort order (Python's
default string comparison, which is codepoint order).

Translating these assigned codes into FreePWING's actual
`halfchars.txt`/`fullchars.txt` line format is TASK-M007's job; this
module only computes the abstract, deterministic mapping.
"""

from __future__ import annotations

from collections.abc import Iterable

_WIDTH_CLASSES = ("narrow", "wide")


class GaijiCodeAssignmentError(ValueError):
    """Raised when gaiji codes cannot be assigned deterministically."""


def assign_gaiji_codes(entries: Iterable[tuple[str, str]]) -> dict[str, str]:
    """Assign each `(sequence, width_class)` entry a deterministic `assigned_code`.

    Returns a mapping from `sequence` to its assigned code
    (`f"{width_class}-{index:04d}"`, 1-based per width class, ordered by
    the sequence's Unicode sort order).
    """
    by_width_class: dict[str, list[str]] = {width_class: [] for width_class in _WIDTH_CLASSES}
    seen_sequences: set[str] = set()
    for sequence, width_class in entries:
        if width_class not in _WIDTH_CLASSES:
            raise GaijiCodeAssignmentError(
                f"width_class must be one of {_WIDTH_CLASSES}: {width_class!r}"
            )
        if sequence in seen_sequences:
            raise GaijiCodeAssignmentError(f"duplicate sequence: {sequence!r}")
        seen_sequences.add(sequence)
        by_width_class[width_class].append(sequence)

    assigned: dict[str, str] = {}
    for width_class, sequences in by_width_class.items():
        for index, sequence in enumerate(sorted(sequences), start=1):
            assigned[sequence] = f"{width_class}-{index:04d}"
    return assigned
