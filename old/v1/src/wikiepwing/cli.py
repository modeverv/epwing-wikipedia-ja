"""Command-line interface for the Wikipedia EPWING Builder."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from wikiepwing.doctor import doctor_payload, run_doctor
from wikiepwing.dump.downloader import (
    DownloadError,
    download,
    dump_url,
    fetch_sha1sums_entry,
    register_local,
    write_remote_manifest,
)
from wikiepwing.epwing.verify import inspect_archive
from wikiepwing.pipeline.export import export_records
from wikiepwing.pipeline.ingest import ingest_xml


def _default_config_path() -> Path:
    return Path(os.environ.get("WIKIEPWING_CONFIG_DIR", "config")) / "default.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wikiepwing", description="Wikipedia EPWING Builder")
    subcommands = parser.add_subparsers(dest="command", required=True)
    doctor = subcommands.add_parser("doctor", help="validate configuration and runtime directories")
    doctor.add_argument("--config", type=Path, default=_default_config_path())
    doctor.add_argument("--json", action="store_true", dest="as_json")
    download_parser = subcommands.add_parser(
        "download", help="acquire or register a Wikimedia dump"
    )
    download_parser.add_argument("--project", default="jawiki")
    download_parser.add_argument("--date", default="latest")
    download_parser.add_argument("--local", type=Path)
    download_parser.add_argument("--url")
    download_parser.add_argument("--sha1")
    download_parser.add_argument("--data-dir", type=Path, default=Path("/data"))
    ingest = subcommands.add_parser("ingest", help="stream a dump into raw-page SQLite storage")
    ingest.add_argument("--input", type=Path, required=True)
    ingest.add_argument("--database", type=Path, required=True)
    ingest.add_argument("--batch-size", type=int, default=500)
    inspect = subcommands.add_parser("inspect", help="independently verify an EPWING package")
    inspect.add_argument("archive", type=Path)
    build = subcommands.add_parser(
        "build", help="build a text-only EPWING package from adapter records"
    )
    build.add_argument("--records", type=Path, required=True)
    build.add_argument("--output", type=Path, default=Path("/output/wikiepwing-epwing.zip"))
    export = subcommands.add_parser("export-records", help="render raw stored pages for FreePWING")
    export.add_argument("--database", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a CLI command and return a POSIX exit status."""
    arguments = build_parser().parse_args(argv)
    if arguments.command == "doctor":
        results = run_doctor(arguments.config)
        payload = doctor_payload(results)
        if arguments.as_json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            for check in results:
                status = "ok" if check.ok else "failed"
                print(f"{status:6} {check.name}: {check.detail}")
        return 0 if payload["ok"] else 1
    if arguments.command == "download":
        manifest_path = arguments.data_dir / "manifests" / "dump.json"
        try:
            if arguments.local is not None:
                manifest = register_local(
                    arguments.local, arguments.project, arguments.date, manifest_path
                )
            else:
                url = arguments.url or dump_url(arguments.project, arguments.date)
                checksum, checksum_filename = fetch_sha1sums_entry(url)
                resolved_date = arguments.date
                if arguments.url is None and arguments.date == "latest":
                    resolved_date = checksum_filename.split("-", 2)[1]
                    url = dump_url(arguments.project, resolved_date)
                target = arguments.data_dir / "dumps" / checksum_filename
                downloaded = download(url, target, arguments.sha1 or checksum)
                manifest = write_remote_manifest(
                    downloaded, arguments.project, resolved_date, url, manifest_path
                )
            print(json.dumps(asdict(manifest), ensure_ascii=False, sort_keys=True))
            return 0
        except DownloadError as error:
            print(f"download failed: {error}", file=sys.stderr)
            return 1
    if arguments.command == "ingest":
        try:
            count = ingest_xml(arguments.input, arguments.database, arguments.batch_size)
        except (OSError, ValueError) as error:
            print(f"ingest failed: {error}", file=sys.stderr)
            return 1
        print(
            json.dumps(
                {"database": str(arguments.database), "pages_ingested": count}, sort_keys=True
            )
        )
        return 0
    if arguments.command == "inspect":
        inspection = inspect_archive(arguments.archive)
        print(json.dumps(asdict(inspection), ensure_ascii=False, sort_keys=True))
        return 0 if inspection.ok else 1
    if arguments.command == "build":
        script = Path("/workspace/docker/scripts/build-records.sh")
        try:
            subprocess.run(
                ["sh", str(script), str(arguments.records), str(arguments.output)], check=True
            )
        except subprocess.CalledProcessError as error:
            print(f"build failed: {error}", file=sys.stderr)
            return 1
        print(json.dumps({"archive": str(arguments.output)}, sort_keys=True))
        return 0
    if arguments.command == "export-records":
        try:
            count = export_records(arguments.database, arguments.output)
        except (OSError, ValueError) as error:
            print(f"export failed: {error}", file=sys.stderr)
            return 1
        print(
            json.dumps(
                {"articles_exported": count, "records": str(arguments.output)}, sort_keys=True
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
