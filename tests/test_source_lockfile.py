from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from wikiepwing.source.lockfile import (
    SourceLockAcquirer,
    SourceLockError,
    SourceLockFile,
    build_source_lock,
    canonical_json,
    parse_source_lock,
)

SCHEMA_PATH = Path("schemas/source-lock.schema.json")


def _load_schema() -> dict[str, Any]:
    import json

    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _file(**overrides: object) -> SourceLockFile:
    defaults: dict[str, object] = {
        "relative_path": "jawiki_namespace_0_chunk_0.ndjson.gz",
        "chunk_identifier": "jawiki_namespace_0_chunk_0",
        "size_bytes": 1024,
        "sha256": "a" * 64,
        "media_type": "application/gzip",
    }
    defaults.update(overrides)
    return SourceLockFile(**defaults)  # type: ignore[arg-type]


def _acquirer(**overrides: object) -> SourceLockAcquirer:
    defaults: dict[str, object] = {
        "name": "wikiepwing",
        "version": "0.1.0",
        "git_commit": "abc1234",
    }
    defaults.update(overrides)
    return SourceLockAcquirer(**defaults)  # type: ignore[arg-type]


def _build(**overrides: object) -> Any:
    defaults: dict[str, object] = {
        "provider": "wikimedia-enterprise-snapshot",
        "project": "jawiki",
        "namespace": 0,
        "snapshot_identifier": "jawiki_namespace_0",
        "snapshot_version": "35061ecbd3bc55c31cffd4b46838673d",
        "date_modified": datetime(2026, 7, 1, 0, 50, 43, tzinfo=UTC),
        "downloaded_at": datetime(2026, 7, 14, 1, 0, 0, tzinfo=UTC),
        "files": (_file(),),
        "supplements": (),
        "metadata_response_sha256": "b" * 64,
        "acquirer": _acquirer(),
    }
    defaults.update(overrides)
    return build_source_lock(**defaults)  # type: ignore[arg-type]


def test_builds_valid_lock_and_matches_schema() -> None:
    lock = _build()

    jsonschema.Draft202012Validator(
        _load_schema(), format_checker=jsonschema.FormatChecker()
    ).validate(lock.payload())


def test_canonical_json_is_deterministic() -> None:
    first = canonical_json(_build())
    second = canonical_json(_build())

    assert first == second
    assert first.endswith(b"\n")


def test_canonical_json_round_trips() -> None:
    lock = _build()

    parsed = parse_source_lock(canonical_json(lock))

    assert parsed == lock


def test_empty_files_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="files must not be empty"):
        _build(files=())


def test_duplicate_chunk_identifier_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="duplicate chunk_identifier"):
        _build(
            files=(
                _file(relative_path="a.ndjson.gz"),
                _file(relative_path="b.ndjson.gz"),
            )
        )


def test_duplicate_relative_path_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="duplicate relative_path"):
        _build(
            files=(
                _file(chunk_identifier="chunk_0"),
                _file(chunk_identifier="chunk_1"),
            )
        )


def test_absolute_relative_path_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="relative path"):
        _build(files=(_file(relative_path="/etc/passwd"),))


def test_parent_traversal_relative_path_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="must not contain"):
        _build(files=(_file(relative_path="../escape.ndjson.gz"),))


def test_latest_snapshot_version_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="latest"):
        _build(snapshot_version="latest")


def test_negative_namespace_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="namespace"):
        _build(namespace=-1)


def test_negative_size_bytes_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="size_bytes"):
        _build(files=(_file(size_bytes=-1),))


def test_invalid_file_sha256_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="sha256"):
        _build(files=(_file(sha256="not-hex"),))


def test_invalid_metadata_response_sha256_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="metadata_response_sha256"):
        _build(metadata_response_sha256="not-hex")


def test_naive_date_modified_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="timezone"):
        _build(date_modified=datetime(2026, 7, 1, 0, 0, 0))


def test_naive_downloaded_at_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="timezone"):
        _build(downloaded_at=datetime(2026, 7, 14, 0, 0, 0))


def test_invalid_git_commit_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="git_commit"):
        _build(acquirer=_acquirer(git_commit="not-hex!"))


def test_empty_acquirer_name_is_rejected() -> None:
    with pytest.raises(SourceLockError, match="acquirer.name"):
        _build(acquirer=_acquirer(name=""))


def test_non_utc_timezone_is_normalized_in_canonical_json() -> None:
    plus_nine = timezone(timedelta(hours=9))
    lock = _build(date_modified=datetime(2026, 7, 1, 9, 50, 43, tzinfo=plus_nine))

    payload = lock.payload()

    assert payload["date_modified"] == "2026-07-01T00:50:43Z"


def test_parse_rejects_malformed_json() -> None:
    with pytest.raises(SourceLockError, match="not valid JSON"):
        parse_source_lock(b"not json")


def test_parse_rejects_non_object() -> None:
    with pytest.raises(SourceLockError, match="JSON object"):
        parse_source_lock(b"[]")


def test_parse_rejects_wrong_schema_version() -> None:
    lock = _build()
    payload = lock.payload()
    payload["schema_version"] = 2
    import json

    with pytest.raises(SourceLockError, match="schema_version"):
        parse_source_lock(json.dumps(payload).encode("utf-8"))


def test_parse_rejects_missing_required_field() -> None:
    lock = _build()
    payload = lock.payload()
    del payload["provider"]
    import json

    with pytest.raises(SourceLockError, match="provider"):
        parse_source_lock(json.dumps(payload).encode("utf-8"))
