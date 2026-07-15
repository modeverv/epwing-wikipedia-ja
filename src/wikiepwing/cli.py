"""Command-line entry point for wikiepwing."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from wikiepwing import __version__
from wikiepwing.config import load_config
from wikiepwing.doctor import render_doctor_text, run_doctor
from wikiepwing.ingest.database import connect_raw_database
from wikiepwing.ingest.orchestrate import run_ingest
from wikiepwing.ingest.validate import ValidationLimits
from wikiepwing.ingest.verify import verify_raw_database
from wikiepwing.media.cache import MediaCache
from wikiepwing.media.downloader import SecureMediaDownloader
from wikiepwing.media.freepwing_graphics import GraphicBuildEntry, write_graphics_build_files
from wikiepwing.media.orchestrate import (
    convert_media,
    fetch_media,
    plan_media,
    read_fetch_report,
    write_fetch_report,
)
from wikiepwing.model.validate import ModelValidationLimits
from wikiepwing.normalize.orchestrate import DEFAULT_BATCH_SIZE, run_normalize
from wikiepwing.normalize.pipeline import NormalizeOptions
from wikiepwing.pipeline.build import STAGE_ORDER, is_forced_stage, stages_from
from wikiepwing.reference.entries import EbEntryAdapter, sample_reference_entries
from wikiepwing.reference.inventory import (
    build_reference_inventory,
    write_reference_inventory,
)
from wikiepwing.reference.report import write_reference_report
from wikiepwing.reference.searches import EbSearchAdapter, run_reference_searches
from wikiepwing.render.generate import run_generate
from wikiepwing.render.verify import verify_entries_jsonl
from wikiepwing.secrets import load_enterprise_secrets
from wikiepwing.source.acquire import acquire_snapshot
from wikiepwing.source.auth import EnterpriseAuthClient, HttpAuthTransport
from wikiepwing.source.downloader import HttpChunkTransport, ResumableChunkDownloader
from wikiepwing.source.enterprise import HttpSnapshotMetadataTransport, SnapshotMetadataClient
from wikiepwing.source.inspect import inspect_source
from wikiepwing.source.lockfile import SourceLockError, parse_source_lock
from wikiepwing.source.register import LocalSourceFile, register_local_source

_GIT_COMMIT = re.compile(r"^[0-9a-f]{4,64}$")


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level command-line parser."""
    parser = argparse.ArgumentParser(
        prog="wikiepwing",
        description="Build Japanese Wikipedia dictionaries in EPWING format.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")
    doctor = subparsers.add_parser("doctor", help="check the build environment")
    doctor.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    doctor.add_argument("--json", action="store_true", help="emit the schema-versioned JSON report")
    inventory = subparsers.add_parser(
        "reference-inventory", help="write a bounded metadata inventory of the reference EPWING"
    )
    inventory.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    inventory.add_argument(
        "--output",
        type=Path,
        help="JSON output path (default: paths.reports/reference-inventory.json)",
    )
    search = subparsers.add_parser(
        "reference-search", help="execute and persist the fixed reference query set"
    )
    search.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    search.add_argument(
        "--query-set",
        type=Path,
        help="fixed query TOML (default: config/query-set.toml)",
    )
    search.add_argument(
        "--database",
        type=Path,
        help="output SQLite path (default: paths.work/reference.sqlite3)",
    )
    search.add_argument(
        "--adapter",
        type=Path,
        default=Path("/opt/eb/bin/wikiepwing-eb-search"),
        help="absolute path to the EB search adapter",
    )
    search.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="timeout applied independently to each query and search mode",
    )
    sample = subparsers.add_parser(
        "reference-sample", help="read bounded rank-one entry samples into the reference DB"
    )
    sample.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    sample.add_argument(
        "--database",
        type=Path,
        help="reference SQLite path (default: paths.work/reference.sqlite3)",
    )
    sample.add_argument(
        "--adapter",
        type=Path,
        default=Path("/opt/eb/bin/wikiepwing-eb-entry"),
        help="absolute path to the EB entry adapter",
    )
    sample.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="timeout applied independently to each sampled entry",
    )
    sample.add_argument(
        "--max-body-bytes",
        type=int,
        default=262144,
        help="maximum decoded EB bytes read per sampled entry",
    )
    report = subparsers.add_parser(
        "reference-report", help="write JSON, HTML, and manual reference review artifacts"
    )
    report.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    report.add_argument(
        "--database",
        type=Path,
        help="reference SQLite path (default: paths.work/reference.sqlite3)",
    )
    report.add_argument(
        "--output-directory",
        type=Path,
        help="report directory (default: paths.reports)",
    )
    acquire = subparsers.add_parser(
        "acquire", help="resolve, download, verify, and lock a Wikimedia Enterprise Snapshot"
    )
    acquire.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    acquire.add_argument(
        "--namespace",
        type=int,
        help="override configured source.namespace",
    )
    acquire.add_argument(
        "--snapshot-version",
        type=str,
        help="override configured source.snapshot ('latest' or a concrete version)",
    )
    acquire.add_argument(
        "--git-commit",
        type=str,
        help="git commit recorded in source.lock.json (default: `git rev-parse HEAD`)",
    )
    register = subparsers.add_parser(
        "register-local-source",
        help="register predownloaded Snapshot files without re-fetching them",
    )
    register.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    register.add_argument("--project", type=str, help="override configured project")
    register.add_argument("--namespace", type=int, help="override configured source.namespace")
    register.add_argument(
        "--snapshot-identifier",
        type=str,
        required=True,
        help="Snapshot identifier, e.g. jawiki_namespace_0",
    )
    register.add_argument(
        "--snapshot-version",
        type=str,
        required=True,
        help="concrete Snapshot version identifier (not 'latest')",
    )
    register.add_argument(
        "--date-modified",
        type=str,
        required=True,
        help="RFC3339 timestamp for this Snapshot version",
    )
    register.add_argument(
        "--file",
        action="append",
        default=[],
        required=True,
        metavar="PATH:CHUNK_IDENTIFIER[:SHA256]",
        help="predownloaded file to register; may be repeated",
    )
    register.add_argument(
        "--copy",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="copy the file into paths.sources (default) or symlink to it in place",
    )
    register.add_argument(
        "--git-commit",
        type=str,
        help="git commit recorded in source.lock.json (default: `git rev-parse HEAD`)",
    )
    inspect = subparsers.add_parser(
        "inspect-source", help="re-verify and sample an acquired Snapshot's source.lock.json"
    )
    inspect.add_argument(
        "--lock-path",
        type=Path,
        required=True,
        help="path to a source.lock.json to inspect",
    )
    inspect.add_argument(
        "--sample-lines",
        type=int,
        default=5,
        help="number of NDJSON records to sample per chunk (default: 5)",
    )
    ingest = subparsers.add_parser("ingest", help="stream a Snapshot's chunks into raw.sqlite3")
    ingest.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    ingest.add_argument(
        "--lock-path",
        type=Path,
        required=True,
        help="path to the acquired Snapshot's source.lock.json",
    )
    ingest.add_argument(
        "--namespace",
        type=int,
        help="override configured source.namespace as the expected article namespace",
    )
    ingest.add_argument(
        "--run-id",
        type=str,
        help="run identifier recorded in the stage manifest (default: generated)",
    )
    ingest.add_argument(
        "--raw-database",
        type=Path,
        help="raw.sqlite3 output path (default: paths.work/raw.sqlite3)",
    )
    ingest.add_argument(
        "--manifest-path",
        type=Path,
        help=(
            "stage manifest output path "
            "(default: paths.work/runs/<run-id>/manifests/30-ingest.json)"
        ),
    )
    ingest.add_argument(
        "--batch-size",
        type=int,
        help="override configured ingest.batch_size",
    )
    ingest.add_argument(
        "--git-commit",
        type=str,
        help="git commit recorded in the manifest (default: `git rev-parse HEAD`)",
    )
    ingest.add_argument(
        "--force",
        action="store_true",
        help="proceed even if the manifest shows a previous run still 'running'",
    )
    verify_raw = subparsers.add_parser(
        "verify-raw", help="verify a raw.sqlite3: integrity, foreign keys, counts, samples"
    )
    verify_raw.add_argument(
        "--raw-database",
        type=Path,
        required=True,
        help="path to the raw.sqlite3 to verify",
    )
    verify_raw.add_argument(
        "--sample-size",
        type=int,
        default=20,
        help="number of accepted articles to sample-decompress (default: 20)",
    )
    normalize = subparsers.add_parser(
        "normalize", help="normalize accepted raw articles into model.sqlite3"
    )
    normalize.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    normalize.add_argument(
        "--raw-database",
        type=Path,
        help="raw.sqlite3 input path (default: paths.work/raw.sqlite3)",
    )
    normalize.add_argument(
        "--model-database",
        type=Path,
        help="model.sqlite3 output path (default: paths.work/model.sqlite3)",
    )
    normalize.add_argument(
        "--run-id",
        type=str,
        help="run identifier recorded in the stage manifest (default: generated)",
    )
    normalize.add_argument(
        "--manifest-path",
        type=Path,
        help=(
            "stage manifest output path "
            "(default: paths.work/runs/<run-id>/manifests/40-normalize.json)"
        ),
    )
    normalize.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="articles per write transaction (default: 500)",
    )
    normalize.add_argument(
        "--git-commit",
        type=str,
        help="git commit recorded in the manifest (default: `git rev-parse HEAD`)",
    )
    normalize.add_argument(
        "--force",
        action="store_true",
        help="proceed even if the manifest shows a previous run still 'running'",
    )
    generate = subparsers.add_parser(
        "generate", help="render non-rejected model.sqlite3 articles into FreePWING entries.jsonl"
    )
    generate.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    generate.add_argument(
        "--model-database",
        type=Path,
        help="model.sqlite3 input path (default: paths.work/model.sqlite3)",
    )
    generate.add_argument(
        "--entries-output",
        type=Path,
        help="entries.jsonl output path (default: paths.output/entries.jsonl)",
    )
    generate.add_argument(
        "--run-id",
        type=str,
        help="run identifier recorded in the stage manifest (default: generated)",
    )
    generate.add_argument(
        "--manifest-path",
        type=Path,
        help=(
            "stage manifest output path "
            "(default: paths.work/runs/<run-id>/manifests/50-generate.json)"
        ),
    )
    generate.add_argument(
        "--git-commit",
        type=str,
        help="git commit recorded in the manifest (default: `git rev-parse HEAD`)",
    )
    generate.add_argument(
        "--force",
        action="store_true",
        help="proceed even if the manifest shows a previous run still 'running'",
    )
    build = subparsers.add_parser(
        "build", help="chain ingest -> normalize -> generate, reusing completed stages"
    )
    build.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    build.add_argument(
        "--lock-path",
        type=Path,
        required=True,
        help="path to the acquired Snapshot's source.lock.json",
    )
    build.add_argument(
        "--namespace",
        type=int,
        help="override configured source.namespace as the expected article namespace",
    )
    build.add_argument(
        "--run-id",
        type=str,
        help="run identifier recorded in each stage manifest (default: generated)",
    )
    build.add_argument(
        "--git-commit",
        type=str,
        help="git commit recorded in each manifest (default: `git rev-parse HEAD`)",
    )
    build.add_argument(
        "--from-stage",
        choices=STAGE_ORDER,
        help="skip stages before this one, assuming they already completed",
    )
    build.add_argument(
        "--force-stage",
        choices=STAGE_ORDER,
        help="force this one stage to rerun even if its previous manifest is reusable",
    )
    verify = subparsers.add_parser(
        "verify", help="verify entries.jsonl: empty/duplicate tags, headwords, unknown targets"
    )
    verify.add_argument(
        "--entries",
        type=Path,
        required=True,
        help="path to the entries.jsonl to verify",
    )
    image_plan = subparsers.add_parser(
        "image-plan", help="list every non-rejected article's selected media from model.sqlite3"
    )
    image_plan.add_argument(
        "--model-database",
        type=Path,
        required=True,
        help="model.sqlite3 input path",
    )
    image_fetch = subparsers.add_parser(
        "image-fetch", help="download and validate/sanitize an image-plan's unique media URLs"
    )
    image_fetch.add_argument(
        "--config",
        action="append",
        default=[],
        type=Path,
        help="additional TOML configuration applied after defaults",
    )
    image_fetch.add_argument(
        "--model-database",
        type=Path,
        required=True,
        help="model.sqlite3 input path",
    )
    image_fetch.add_argument(
        "--originals-dir",
        type=Path,
        required=True,
        help="directory to store fetched originals in, keyed by content hash",
    )
    image_fetch.add_argument(
        "--report",
        type=Path,
        required=True,
        help="fetch report JSON output path (read back by image-convert)",
    )
    image_convert = subparsers.add_parser(
        "image-convert", help="raster-convert an image-fetch report's originals to BMP graphics"
    )
    image_convert.add_argument(
        "--originals-dir",
        type=Path,
        required=True,
        help="directory image-fetch stored originals in",
    )
    image_convert.add_argument(
        "--report",
        type=Path,
        required=True,
        help="fetch report JSON written by image-fetch",
    )
    image_convert.add_argument(
        "--cache-dir",
        type=Path,
        required=True,
        help="directory for the content-addressed BMP conversion cache",
    )
    image_convert.add_argument(
        "--graphics-dir",
        type=Path,
        required=True,
        help="directory to write FreePWING graphics build files (*.bmp, cgraphs.txt) into",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the wikiepwing command-line interface."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    command = cast(str | None, arguments.command)
    if command == "doctor":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        report = run_doctor(_default_config_path(), overrides)
        if cast(bool, arguments.json):
            print(json.dumps(report.payload(), ensure_ascii=False, sort_keys=True))
        else:
            print(render_doctor_text(report), end="")
        return report.exit_code
    if command == "reference-inventory":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)
        inventory = build_reference_inventory(config.paths.reference)
        requested_output = cast(Path | None, arguments.output)
        output = requested_output or config.paths.reports / "reference-inventory.json"
        print(write_reference_inventory(inventory, output))
        return 0
    if command == "reference-search":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)
        requested_query_set = cast(Path | None, arguments.query_set)
        requested_database = cast(Path | None, arguments.database)
        query_set = requested_query_set or _default_query_set_path()
        database = requested_database or config.paths.work / "reference.sqlite3"
        search_adapter = EbSearchAdapter(
            cast(Path, arguments.adapter),
            timeout_seconds=cast(float, arguments.timeout_seconds),
        )
        print(run_reference_searches(config.paths.reference, query_set, database, search_adapter))
        return 0
    if command == "reference-sample":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)
        requested_database = cast(Path | None, arguments.database)
        database = requested_database or config.paths.work / "reference.sqlite3"
        entry_adapter = EbEntryAdapter(
            cast(Path, arguments.adapter),
            timeout_seconds=cast(float, arguments.timeout_seconds),
        )
        print(
            sample_reference_entries(
                database,
                config.paths.reference,
                entry_adapter,
                max_body_bytes=cast(int, arguments.max_body_bytes),
            )
        )
        return 0
    if command == "reference-report":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)
        requested_database = cast(Path | None, arguments.database)
        requested_output = cast(Path | None, arguments.output_directory)
        database = requested_database or config.paths.work / "reference.sqlite3"
        output = requested_output or config.paths.reports
        for path in write_reference_report(database, output):
            print(path)
        return 0
    if command == "acquire":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)
        secrets = load_enterprise_secrets(os.environ)
        source_section = config.section("source")
        enterprise_section = cast(Mapping[str, object], source_section["enterprise"])
        namespace = cast(int | None, arguments.namespace)
        if namespace is None:
            namespace = cast(int, source_section["namespace"])
        requested_version = cast(str | None, arguments.snapshot_version) or cast(
            str, source_section["snapshot"]
        )
        git_commit = cast(str | None, arguments.git_commit) or _resolve_git_commit()
        request_timeout_seconds = float(cast(int, enterprise_section["request_timeout_seconds"]))
        auth_client = EnterpriseAuthClient(
            HttpAuthTransport(cast(str, enterprise_section["auth_base"])),
            timeout_seconds=request_timeout_seconds,
        )
        metadata_client = SnapshotMetadataClient(
            HttpSnapshotMetadataTransport(cast(str, enterprise_section["api_base"])),
            timeout_seconds=request_timeout_seconds,
        )
        downloader = ResumableChunkDownloader(
            HttpChunkTransport(cast(str, enterprise_section["api_base"])),
            timeout_seconds=float(cast(int, enterprise_section["download_timeout_seconds"])),
            max_retries=int(cast(int, enterprise_section["max_retries"])),
        )
        result = acquire_snapshot(
            secrets,
            auth_client=auth_client,
            metadata_client=metadata_client,
            downloader=downloader,
            project=config.project,
            namespace=namespace,
            requested_version=requested_version,
            sources_root=config.paths.sources,
            acquirer_name="wikiepwing",
            acquirer_version=__version__,
            acquirer_git_commit=git_commit,
        )
        print(result.lock_path)
        return 0
    if command == "register-local-source":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)
        source_section = config.section("source")
        project = cast(str | None, arguments.project) or config.project
        namespace = cast(int | None, arguments.namespace)
        if namespace is None:
            namespace = cast(int, source_section["namespace"])
        git_commit = cast(str | None, arguments.git_commit) or _resolve_git_commit()
        files = [_parse_file_argument(value) for value in cast(list[str], arguments.file)]
        result = register_local_source(
            files,
            project=project,
            namespace=namespace,
            snapshot_identifier=cast(str, arguments.snapshot_identifier),
            snapshot_version=cast(str, arguments.snapshot_version),
            date_modified=_parse_date_modified(cast(str, arguments.date_modified)),
            sources_root=config.paths.sources,
            copy=cast(bool, arguments.copy),
            acquirer_name="wikiepwing",
            acquirer_version=__version__,
            acquirer_git_commit=git_commit,
        )
        print(result.lock_path)
        return 0
    if command == "inspect-source":
        inspection = inspect_source(
            cast(Path, arguments.lock_path).resolve(),
            sample_lines=cast(int, arguments.sample_lines),
        )
        print(json.dumps(inspection.payload(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if inspection.ok else 1
    if command == "ingest":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)
        lock_path = cast(Path, arguments.lock_path).resolve()
        try:
            lock = parse_source_lock(lock_path.read_bytes())
        except (OSError, SourceLockError) as error:
            raise SystemExit(f"cannot read source lock {lock_path}: {error}") from error

        ingest_section = config.section("ingest")
        namespace = cast(int | None, arguments.namespace)
        if namespace is None:
            namespace = cast(int, config.section("source")["namespace"])
        limits = ValidationLimits.from_config(config, expected_namespace_id=namespace)
        batch_size = cast(int | None, arguments.batch_size) or cast(
            int, ingest_section["batch_size"]
        )
        run_id = cast(str | None, arguments.run_id) or (
            f"{config.project}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
        )
        raw_database_path = cast(Path | None, arguments.raw_database) or (
            config.paths.work / "raw.sqlite3"
        )
        manifest_path = cast(Path | None, arguments.manifest_path) or (
            config.paths.work / "runs" / run_id / "manifests" / "30-ingest.json"
        )
        git_commit = cast(str | None, arguments.git_commit) or _resolve_git_commit()

        ingest_result = run_ingest(
            lock,
            snapshot_directory=lock_path.parent,
            raw_database_path=raw_database_path,
            migrations_path=None,
            manifest_path=manifest_path,
            run_id=run_id,
            validation_limits=limits,
            zstd_level=cast(int, ingest_section["zstd_level"]),
            batch_size=batch_size,
            git_commit=git_commit,
            force=cast(bool, arguments.force),
            on_progress=lambda metrics: print(
                f"records_read={metrics.records_read} "
                f"records_written={metrics.records_written} "
                f"records_rejected={metrics.records_rejected}",
                file=sys.stderr,
            ),
        )
        print(ingest_result.manifest_path)
        return 0 if ingest_result.manifest.status == "complete" else 1
    if command == "verify-raw":
        connection = connect_raw_database(cast(Path, arguments.raw_database).resolve())
        try:
            verification = verify_raw_database(
                connection, sample_size=cast(int, arguments.sample_size)
            )
        finally:
            connection.close()
        print(json.dumps(verification.payload(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if verification.ok else 1
    if command == "normalize":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)

        normalize_section = config.section("normalize")
        model_validation_limits = ModelValidationLimits.from_config(config)
        normalize_options = NormalizeOptions(
            max_dom_depth=cast(int, normalize_section["max_dom_depth"]),
            html_recover=cast(bool, normalize_section["html_recover"]),
            remove_edit_ui=cast(bool, normalize_section["remove_edit_ui"]),
            remove_navboxes=cast(bool, normalize_section["remove_navboxes"]),
            remove_authority_control=cast(bool, normalize_section["remove_authority_control"]),
            images_enabled=cast(bool, config.section("images")["enabled"]),
        )
        run_id = cast(str | None, arguments.run_id) or (
            f"{config.project}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
        )
        raw_database_path = cast(Path | None, arguments.raw_database) or (
            config.paths.work / "raw.sqlite3"
        )
        model_database_path = cast(Path | None, arguments.model_database) or (
            config.paths.work / "model.sqlite3"
        )
        manifest_path = cast(Path | None, arguments.manifest_path) or (
            config.paths.work / "runs" / run_id / "manifests" / "40-normalize.json"
        )
        git_commit = cast(str | None, arguments.git_commit) or _resolve_git_commit()

        normalize_result = run_normalize(
            raw_database_path=raw_database_path,
            model_database_path=model_database_path,
            model_migrations_path=None,
            manifest_path=manifest_path,
            run_id=run_id,
            model_validation_limits=model_validation_limits,
            normalize_options=normalize_options,
            batch_size=cast(int, arguments.batch_size),
            git_commit=git_commit,
            force=cast(bool, arguments.force),
            on_progress=lambda metrics: print(
                f"articles_read={metrics.articles_read} "
                f"articles_written={metrics.articles_written} "
                f"articles_rejected={metrics.articles_rejected}",
                file=sys.stderr,
            ),
        )
        print(normalize_result.manifest_path)
        return 0 if normalize_result.manifest.status == "complete" else 1
    if command == "generate":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)

        run_id = cast(str | None, arguments.run_id) or (
            f"{config.project}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
        )
        model_database_path = cast(Path | None, arguments.model_database) or (
            config.paths.work / "model.sqlite3"
        )
        entries_path = cast(Path | None, arguments.entries_output) or (
            config.paths.output / "entries.jsonl"
        )
        manifest_path = cast(Path | None, arguments.manifest_path) or (
            config.paths.work / "runs" / run_id / "manifests" / "50-generate.json"
        )
        git_commit = cast(str | None, arguments.git_commit) or _resolve_git_commit()

        generate_result = run_generate(
            model_database_path=model_database_path,
            entries_path=entries_path,
            manifest_path=manifest_path,
            run_id=run_id,
            git_commit=git_commit,
            force=cast(bool, arguments.force),
            on_progress=lambda metrics: print(
                f"articles_read={metrics.articles_read} "
                f"entries_written={metrics.entries_written} "
                f"articles_skipped={metrics.articles_skipped}",
                file=sys.stderr,
            ),
        )
        print(generate_result.manifest_path)
        return 0 if generate_result.manifest.status == "complete" else 1
    if command == "build":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)
        lock_path = cast(Path, arguments.lock_path).resolve()
        try:
            lock = parse_source_lock(lock_path.read_bytes())
        except (OSError, SourceLockError) as error:
            raise SystemExit(f"cannot read source lock {lock_path}: {error}") from error

        run_id = cast(str | None, arguments.run_id) or (
            f"{config.project}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
        )
        git_commit = cast(str | None, arguments.git_commit) or _resolve_git_commit()
        from_stage = cast(str | None, arguments.from_stage)
        force_stage = cast(str | None, arguments.force_stage)
        stages = stages_from(from_stage)

        raw_database_path = config.paths.work / "raw.sqlite3"
        model_database_path = config.paths.work / "model.sqlite3"
        entries_path = config.paths.output / "entries.jsonl"
        manifests_root = config.paths.work / "runs" / run_id / "manifests"

        if "ingest" in stages:
            ingest_section = config.section("ingest")
            namespace = cast(int | None, arguments.namespace)
            if namespace is None:
                namespace = cast(int, config.section("source")["namespace"])
            limits = ValidationLimits.from_config(config, expected_namespace_id=namespace)
            ingest_result = run_ingest(
                lock,
                snapshot_directory=lock_path.parent,
                raw_database_path=raw_database_path,
                migrations_path=None,
                manifest_path=manifests_root / "30-ingest.json",
                run_id=run_id,
                validation_limits=limits,
                zstd_level=cast(int, ingest_section["zstd_level"]),
                batch_size=cast(int, ingest_section["batch_size"]),
                git_commit=git_commit,
                force=is_forced_stage("ingest", force_stage),
            )
            print(ingest_result.manifest_path)
            if ingest_result.manifest.status != "complete":
                return 1

        if "normalize" in stages:
            normalize_section = config.section("normalize")
            normalize_options = NormalizeOptions(
                max_dom_depth=cast(int, normalize_section["max_dom_depth"]),
                html_recover=cast(bool, normalize_section["html_recover"]),
                remove_edit_ui=cast(bool, normalize_section["remove_edit_ui"]),
                remove_navboxes=cast(bool, normalize_section["remove_navboxes"]),
                remove_authority_control=cast(bool, normalize_section["remove_authority_control"]),
                images_enabled=cast(bool, config.section("images")["enabled"]),
            )
            normalize_result = run_normalize(
                raw_database_path=raw_database_path,
                model_database_path=model_database_path,
                model_migrations_path=None,
                manifest_path=manifests_root / "40-normalize.json",
                run_id=run_id,
                model_validation_limits=ModelValidationLimits.from_config(config),
                normalize_options=normalize_options,
                batch_size=DEFAULT_BATCH_SIZE,
                git_commit=git_commit,
                force=is_forced_stage("normalize", force_stage),
            )
            print(normalize_result.manifest_path)
            if normalize_result.manifest.status != "complete":
                return 1

        if "generate" in stages:
            generate_result = run_generate(
                model_database_path=model_database_path,
                entries_path=entries_path,
                manifest_path=manifests_root / "50-generate.json",
                run_id=run_id,
                git_commit=git_commit,
                force=is_forced_stage("generate", force_stage),
            )
            print(generate_result.manifest_path)
            if generate_result.manifest.status != "complete":
                return 1

        return 0
    if command == "verify":
        entries_verification = verify_entries_jsonl(cast(Path, arguments.entries))
        print(
            json.dumps(entries_verification.payload(), ensure_ascii=False, indent=2, sort_keys=True)
        )
        return 0 if entries_verification.ok else 1
    if command == "image-plan":
        plan = plan_media(cast(Path, arguments.model_database))
        payload = [{"page_id": entry.page_id, **entry.media.payload()} for entry in plan]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if command == "image-fetch":
        overrides = list(cast(list[Path], arguments.config))
        environment_config = os.environ.get("WIKIEPWING_CONFIG")
        if environment_config:
            overrides.insert(0, Path(environment_config))
        config = load_config(_default_config_path(), overrides)
        images_section = config.section("images")

        plan = plan_media(cast(Path, arguments.model_database))
        media_downloader = SecureMediaDownloader(
            allowed_hosts=frozenset(cast(list[str], images_section["allowed_hosts"])),
            max_content_length_bytes=cast(int, images_section["max_download_bytes"]),
        )
        outcomes = fetch_media(
            plan,
            downloader=media_downloader,
            max_pixels=cast(int, images_section["max_pixels"]),
            allow_svg=cast(bool, images_section["allow_svg"]),
        )
        write_fetch_report(
            outcomes,
            originals_dir=cast(Path, arguments.originals_dir),
            report_path=cast(Path, arguments.report),
        )
        succeeded = sum(1 for outcome in outcomes if outcome.ok)
        print(f"fetched={succeeded} failed={len(outcomes) - succeeded} total={len(outcomes)}")
        return 0 if succeeded == len(outcomes) else 1
    if command == "image-convert":
        outcomes = read_fetch_report(
            cast(Path, arguments.report), originals_dir=cast(Path, arguments.originals_dir)
        )
        cache = MediaCache(cast(Path, arguments.cache_dir))
        converted = convert_media(outcomes, cache=cache)
        write_graphics_build_files(
            [
                GraphicBuildEntry(name=result.content_hash, bmp_bytes=result.bmp_bytes)
                for result in converted
            ],
            cast(Path, arguments.graphics_dir),
        )
        print(f"converted={len(converted)}")
        return 0
    if command is None and argv is not None and len(argv) > 0:
        parser.error(f"unsupported command: {command}")
    return 0


def _default_config_path() -> Path:
    candidates = (Path.cwd() / "config/default.toml", Path("/app/config/default.toml"))
    return next((path for path in candidates if path.is_file()), candidates[0])


def _default_query_set_path() -> Path:
    candidates = (Path.cwd() / "config/query-set.toml", Path("/app/config/query-set.toml"))
    return next((path for path in candidates if path.is_file()), candidates[0])


def _resolve_git_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise SystemExit(
            f"cannot resolve git commit automatically; pass --git-commit explicitly ({error})"
        ) from error
    commit = completed.stdout.strip()
    if not _GIT_COMMIT.fullmatch(commit):
        raise SystemExit(
            "`git rev-parse HEAD` returned an unexpected value; pass --git-commit explicitly"
        )
    return commit


def _parse_file_argument(value: str) -> LocalSourceFile:
    parts = value.split(":", 2)
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise SystemExit(f"--file must be PATH:CHUNK_IDENTIFIER[:SHA256], got: {value!r}")
    expected_sha256 = parts[2] if len(parts) == 3 and parts[2] else None
    return LocalSourceFile(
        source_path=Path(parts[0]),
        chunk_identifier=parts[1],
        expected_sha256=expected_sha256,
    )


def _parse_date_modified(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise SystemExit(f"--date-modified must be a valid RFC3339 timestamp: {error}") from error
    if parsed.tzinfo is None:
        raise SystemExit("--date-modified must include a timezone")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
