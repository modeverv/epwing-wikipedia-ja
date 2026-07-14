from __future__ import annotations

import json
from pathlib import Path

import pytest

from wikiepwing.model.blocks import block_payload
from wikiepwing.normalize.pipeline import NormalizeOptions, normalize_html

GOLDEN_DIR = Path(__file__).parent / "golden" / "normalize"
_OPTIONS = NormalizeOptions(
    max_dom_depth=64,
    html_recover=True,
    remove_edit_ui=True,
    remove_navboxes=True,
    remove_authority_control=True,
)


def _html_fixtures() -> list[Path]:
    return sorted(GOLDEN_DIR.glob("*.html"))


def test_ten_golden_fixtures_exist() -> None:
    assert len(_html_fixtures()) == 10


@pytest.mark.parametrize("html_path", _html_fixtures(), ids=lambda path: path.stem)
def test_normalize_html_matches_golden_snapshot(html_path: Path) -> None:
    html = html_path.read_text(encoding="utf-8")
    expected = json.loads(html_path.with_suffix(".json").read_text(encoding="utf-8"))

    blocks, diagnostics = normalize_html(html, _OPTIONS)
    actual = [block_payload(block) for block in blocks]

    assert actual == expected
    assert diagnostics == ()
