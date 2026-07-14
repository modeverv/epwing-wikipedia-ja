from __future__ import annotations

import pytest

from wikiepwing.render.entry_id import EntryIdError, compute_entry_id


def test_compute_entry_id_formats_page_id() -> None:
    assert compute_entry_id(12345) == "p12345"


def test_compute_entry_id_formats_single_digit() -> None:
    assert compute_entry_id(1) == "p1"


def test_compute_entry_id_rejects_zero() -> None:
    with pytest.raises(EntryIdError, match="positive"):
        compute_entry_id(0)


def test_compute_entry_id_rejects_negative() -> None:
    with pytest.raises(EntryIdError, match="positive"):
        compute_entry_id(-1)
