from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.build_info import SoftwareProvenance, build_build_info, write_build_info
from wikiepwing.source.lockfile import (
    SourceLockAcquirer,
    SourceLockFile,
    build_source_lock,
)


def _source_lock():  # type: ignore[no-untyped-def]
    return build_source_lock(
        provider="wikimedia-enterprise-snapshot",
        project="jawiki",
        namespace=0,
        snapshot_identifier="jawiki_namespace_0",
        snapshot_version="35061ecbd3bc55c31cffd4b46838673d",
        date_modified=datetime(2026, 7, 1, tzinfo=UTC),
        downloaded_at=datetime(2026, 7, 16, tzinfo=UTC),
        files=(
            SourceLockFile(
                relative_path="jawiki_namespace_0_chunk_0.tar.gz",
                chunk_identifier="jawiki_namespace_0_chunk_0",
                size_bytes=1,
                sha256="0" * 64,
                media_type="application/gzip",
            ),
        ),
        metadata_response_sha256="0" * 64,
        acquirer=SourceLockAcquirer(name="wikiepwing", version="0.1.0", git_commit="abc1234"),
    )


def test_build_build_info_includes_source_lock_fields() -> None:
    payload = build_build_info(
        _source_lock(),
        profile="lite",
        built_at=datetime(2026, 7, 17, tzinfo=UTC),
        software=SoftwareProvenance(
            git_commit="deadbeef", app_image_digest=None, toolchain_image_digest=None
        ),
    )

    assert payload["schema_version"] == 1
    assert payload["project"] == "jawiki"
    assert payload["snapshot_identifier"] == "jawiki_namespace_0"
    assert payload["snapshot_version"] == "35061ecbd3bc55c31cffd4b46838673d"
    assert payload["snapshot_date_modified"] == "2026-07-01T00:00:00Z"
    assert payload["profile"] == "lite"
    assert payload["built_at"] == "2026-07-17T00:00:00Z"


def test_build_build_info_includes_software_provenance() -> None:
    payload = build_build_info(
        _source_lock(),
        profile="full",
        built_at=datetime(2026, 7, 17, tzinfo=UTC),
        software=SoftwareProvenance(
            git_commit="deadbeef",
            app_image_digest="sha256:app",
            toolchain_image_digest="sha256:toolchain",
        ),
    )

    assert payload["software"] == {
        "git_commit": "deadbeef",
        "app_image_digest": "sha256:app",
        "toolchain_image_digest": "sha256:toolchain",
    }


def test_build_build_info_allows_none_image_digests() -> None:
    payload = build_build_info(
        _source_lock(),
        profile="mini",
        built_at=datetime(2026, 7, 17, tzinfo=UTC),
        software=SoftwareProvenance(
            git_commit="deadbeef", app_image_digest=None, toolchain_image_digest=None
        ),
    )

    software = payload["software"]
    assert isinstance(software, dict)
    assert software["app_image_digest"] is None
    assert software["toolchain_image_digest"] is None


def test_build_build_info_rejects_naive_built_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_build_info(
            _source_lock(),
            profile="lite",
            built_at=datetime(2026, 7, 17),
            software=SoftwareProvenance(
                git_commit="deadbeef", app_image_digest=None, toolchain_image_digest=None
            ),
        )


def test_build_build_info_is_json_serializable() -> None:
    payload = build_build_info(
        _source_lock(),
        profile="lite",
        built_at=datetime(2026, 7, 17, tzinfo=UTC),
        software=SoftwareProvenance(
            git_commit="deadbeef", app_image_digest=None, toolchain_image_digest=None
        ),
    )

    json.dumps(payload)


def test_write_build_info_writes_file_atomically(tmp_path: Path) -> None:
    payload = build_build_info(
        _source_lock(),
        profile="lite",
        built_at=datetime(2026, 7, 17, tzinfo=UTC),
        software=SoftwareProvenance(
            git_commit="deadbeef", app_image_digest=None, toolchain_image_digest=None
        ),
    )
    output_path = tmp_path / "BUILD-INFO.json"

    write_build_info(payload, output_path)

    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_write_build_info_creates_missing_directory(tmp_path: Path) -> None:
    payload = build_build_info(
        _source_lock(),
        profile="lite",
        built_at=datetime(2026, 7, 17, tzinfo=UTC),
        software=SoftwareProvenance(
            git_commit="deadbeef", app_image_digest=None, toolchain_image_digest=None
        ),
    )
    output_path = tmp_path / "nested" / "BUILD-INFO.json"

    write_build_info(payload, output_path)

    assert output_path.is_file()
