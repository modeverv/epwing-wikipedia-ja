"""Stage input fingerprint calculation (TASK-I002, ARCHITECTURE.md 7.3 `Stage.input_fingerprints`).

Produces the `sha256:<hex>` strings DATA_CONTRACTS.md 3's manifest `inputs`
field uses (e.g. `"source_lock": "sha256:..."`), so a stage's recorded inputs
reflect the actual content of what it read -- not just a file path -- which
TASK-I005's resume decision needs to detect real input changes.
"""

from __future__ import annotations

from pathlib import Path

from wikiepwing.source.checksums import compute_fingerprint


def compute_input_fingerprint(path: Path) -> str:
    """Return a `sha256:<hex>` content fingerprint for one input file."""
    fingerprint = compute_fingerprint(path)
    return f"sha256:{fingerprint.sha256}"
