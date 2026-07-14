"""Command-line entry point for wikiepwing."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from wikiepwing import __version__
from wikiepwing.config import load_config
from wikiepwing.doctor import render_doctor_text, run_doctor
from wikiepwing.reference.entries import EbEntryAdapter, sample_reference_entries
from wikiepwing.reference.inventory import (
    build_reference_inventory,
    write_reference_inventory,
)
from wikiepwing.reference.report import write_reference_report
from wikiepwing.reference.searches import EbSearchAdapter, run_reference_searches
from wikiepwing.secrets import load_enterprise_secrets
from wikiepwing.source.acquire import acquire_snapshot
from wikiepwing.source.auth import EnterpriseAuthClient, HttpAuthTransport
from wikiepwing.source.downloader import HttpChunkTransport, ResumableChunkDownloader
from wikiepwing.source.enterprise import HttpSnapshotMetadataTransport, SnapshotMetadataClient

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


if __name__ == "__main__":
    raise SystemExit(main())
