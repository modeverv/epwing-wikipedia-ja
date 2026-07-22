"""Read-only verification of the Lookup.el/ndeb EPWING search contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_LOOKUP_SOURCE_BYTES = 2 * 1024 * 1024


class LookupContractError(ValueError):
    """Raised when the expected Lookup search routing cannot be verified."""


@dataclass(frozen=True, slots=True)
class LookupSearchContract:
    default_method: str
    exact_backend_method: str
    prefix_pattern: str
    prefix_backend_method: str
    keyword_pattern: str
    keyword_backend_methods: tuple[str, ...]


def inspect_lookup_search_contract(root: Path) -> LookupSearchContract:
    """Verify exact/prefix/keyword routing from a local Lookup source tree."""
    source_root = root.expanduser().resolve(strict=True)
    if not source_root.is_dir():
        raise LookupContractError(f"Lookup root must be a directory: {source_root}")
    variables = _read_source(source_root / "lookup-vars.el")
    types = _read_source(source_root / "lookup-types.el")
    ndeb = _read_source(source_root / "ndeb.el")

    required = {
        "default exact": (variables, "(defcustom lookup-default-method 'exact"),
        "plain pattern default": (types, "(t (setq method 'default))"),
        "asterisk prefix": (types, "(setq method 'prefix pattern"),
        "at-sign keyword": (types, "(setq method 'keyword pattern"),
        "exact backend": (ndeb, '(exact . "exact")'),
        "prefix backend": (ndeb, '(prefix . "word")'),
        "keyword backend": (ndeb, "set search-method keyword"),
        "cross backend": (ndeb, "set search-method cross"),
    }
    missing = [name for name, (source, token) in required.items() if token not in source]
    if missing:
        raise LookupContractError(f"Lookup search contract token missing: {missing[0]}")
    return LookupSearchContract(
        default_method="exact",
        exact_backend_method="exact",
        prefix_pattern="term*",
        prefix_backend_method="word",
        keyword_pattern="@term",
        keyword_backend_methods=("keyword", "cross"),
    )


def _read_source(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise LookupContractError(f"Lookup source must be a regular non-symlink file: {path}")
    size = path.stat().st_size
    if size < 1 or size > MAX_LOOKUP_SOURCE_BYTES:
        raise LookupContractError(f"Lookup source size limit violated: {path}: {size}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise LookupContractError(f"Lookup source must be UTF-8: {path}: {error}") from error
