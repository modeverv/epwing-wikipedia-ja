from __future__ import annotations

from pathlib import Path

import pytest

from wikiepwing.compatibility.lookup_contract import (
    LookupContractError,
    LookupSearchContract,
    inspect_lookup_search_contract,
)


def _write_lookup_fixture(root: Path) -> None:
    root.mkdir()
    (root / "lookup-vars.el").write_text(
        '(defcustom lookup-default-method \'exact "default")\n', encoding="utf-8"
    )
    (root / "lookup-types.el").write_text(
        """(cond
((string-match "prefix") (setq method 'prefix pattern pattern))
((string-match "keyword") (setq method 'keyword pattern pattern))
(t (setq method 'default)))
""",
        encoding="utf-8",
    )
    (root / "ndeb.el").write_text(
        """'((exact . "exact") (prefix . "word"))
set search-method keyword
set search-method cross
""",
        encoding="utf-8",
    )


def test_lookup_contract_maps_plain_prefix_and_keyword_queries(tmp_path: Path) -> None:
    root = tmp_path / "lookup"
    _write_lookup_fixture(root)

    contract = inspect_lookup_search_contract(root)

    assert contract == LookupSearchContract(
        default_method="exact",
        exact_backend_method="exact",
        prefix_pattern="term*",
        prefix_backend_method="word",
        keyword_pattern="@term",
        keyword_backend_methods=("keyword", "cross"),
    )


def test_lookup_contract_rejects_missing_cross_routing(tmp_path: Path) -> None:
    root = tmp_path / "lookup"
    _write_lookup_fixture(root)
    (root / "ndeb.el").write_text(
        '\'((exact . "exact") (prefix . "word"))\nset search-method keyword\n',
        encoding="utf-8",
    )

    with pytest.raises(LookupContractError, match="cross backend"):
        inspect_lookup_search_contract(root)
