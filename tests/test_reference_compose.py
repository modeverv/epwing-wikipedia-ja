from __future__ import annotations

from pathlib import Path


def test_reference_compose_override_requires_non_creating_read_only_bind() -> None:
    source = Path("compose.reference.yaml").read_text(encoding="utf-8")

    assert "${WIKIEPWING_REFERENCE_PATH:?" in source
    assert "target: /data/reference" in source
    assert "read_only: true" in source
    assert "create_host_path: false" in source
