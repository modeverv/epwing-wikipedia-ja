from __future__ import annotations

import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


class CliTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "wikiepwing.cli", *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_help(self) -> None:
        result = self.run_cli("--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: wikiepwing", result.stdout)

    def test_version(self) -> None:
        result = self.run_cli("--version")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^wikiepwing \d+\.\d+\.\d+\n$")

    def test_reference_inventory_writes_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            reference = temporary / "reference"
            data = reference / "WIKIP" / "DATA"
            data.mkdir(parents=True)
            (reference / "CATALOGS").write_bytes(b"\0" * 2048)
            (data / "HONMON").write_bytes(b"body")
            for path in sorted(reference.rglob("*"), reverse=True):
                path.chmod(0o555 if path.is_dir() else 0o444)
            reference.chmod(0o555)
            output = temporary / "inventory.json"
            config = temporary / "reference.toml"
            config.write_text(f'[paths]\nreference = "{reference}"\n', encoding="utf-8")

            try:
                result = self.run_cli(
                    "reference-inventory",
                    "--config",
                    str(config),
                    "--output",
                    str(output),
                )
            finally:
                for path in sorted(reference.rglob("*"), reverse=True):
                    path.chmod(0o755 if path.is_dir() else 0o644)
                reference.chmod(0o755)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, f"{output.resolve()}\n")
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["subbook_candidates"][0]["name"], "WIKIP")

    def test_reference_search_help(self) -> None:
        result = self.run_cli("reference-search", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--timeout-seconds", result.stdout)
        self.assertIn("--database", result.stdout)

    def test_reference_sample_help(self) -> None:
        result = self.run_cli("reference-sample", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--max-body-bytes", result.stdout)

    def test_reference_report_help(self) -> None:
        result = self.run_cli("reference-report", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--database", result.stdout)
        self.assertIn("--output-directory", result.stdout)

    def test_acquire_help(self) -> None:
        result = self.run_cli("acquire", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--namespace", result.stdout)
        self.assertIn("--snapshot-version", result.stdout)
        self.assertIn("--git-commit", result.stdout)

    def test_register_local_source_help(self) -> None:
        result = self.run_cli("register-local-source", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--file", result.stdout)
        self.assertIn("--copy", result.stdout)
        self.assertIn("--date-modified", result.stdout)

    def test_register_local_source_registers_predownloaded_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            sources = temporary / "sources"
            source_file = temporary / "downloads" / "mine.tar.gz"
            source_file.parent.mkdir(parents=True)
            source_file.write_bytes(b"predownloaded content")
            config = temporary / "register.toml"
            config.write_text(f'[paths]\nsources = "{sources}"\n', encoding="utf-8")

            result = self.run_cli(
                "register-local-source",
                "--config",
                str(config),
                "--namespace",
                "0",
                "--snapshot-identifier",
                "jawiki_namespace_0",
                "--snapshot-version",
                "local-2026-07-14",
                "--date-modified",
                "2026-07-14T00:00:00Z",
                "--file",
                f"{source_file}:jawiki_namespace_0_chunk_0",
                "--git-commit",
                "abc1234",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            lock_path = Path(result.stdout.strip())
            self.assertTrue(lock_path.is_file())
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            self.assertEqual(lock["snapshot_version"], "local-2026-07-14")
            self.assertEqual(lock["files"][0]["relative_path"], "jawiki_namespace_0_chunk_0.tar.gz")

    def test_inspect_source_help(self) -> None:
        result = self.run_cli("inspect-source", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--lock-path", result.stdout)
        self.assertIn("--sample-lines", result.stdout)

    def test_inspect_source_reports_ok_for_registered_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            sources = temporary / "sources"
            tar_path = temporary / "downloads" / "chunk_0.tar.gz"
            tar_path.parent.mkdir(parents=True)
            body = b'{"identifier":"1"}\n'
            with tarfile.open(tar_path, mode="w:gz") as archive:
                info = tarfile.TarInfo(name="chunk_0.ndjson")
                info.size = len(body)
                archive.addfile(info, io.BytesIO(body))
            config = temporary / "register.toml"
            config.write_text(f'[paths]\nsources = "{sources}"\n', encoding="utf-8")

            register_result = self.run_cli(
                "register-local-source",
                "--config",
                str(config),
                "--namespace",
                "0",
                "--snapshot-identifier",
                "jawiki_namespace_0",
                "--snapshot-version",
                "local-2026-07-14",
                "--date-modified",
                "2026-07-14T00:00:00Z",
                "--file",
                f"{tar_path}:jawiki_namespace_0_chunk_0",
                "--git-commit",
                "abc1234",
            )
            self.assertEqual(register_result.returncode, 0, register_result.stderr)
            lock_path = register_result.stdout.strip()

            inspect_result = self.run_cli("inspect-source", "--lock-path", lock_path)

            self.assertEqual(inspect_result.returncode, 0, inspect_result.stderr)
            report = json.loads(inspect_result.stdout)
            self.assertTrue(report["ok"])
            self.assertEqual(
                report["files"][0]["ndjson_sample"]["sample_records"],
                [{"identifier": "1"}],
            )

    def test_ingest_help(self) -> None:
        result = self.run_cli("ingest", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--lock-path", result.stdout)
        self.assertIn("--batch-size", result.stdout)
        self.assertIn("--raw-database", result.stdout)
        self.assertIn("--force", result.stdout)

    def test_ingest_writes_manifest_and_raw_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            sources = temporary / "sources"
            work = temporary / "work"
            tar_path = temporary / "downloads" / "chunk_0.tar.gz"
            tar_path.parent.mkdir(parents=True)
            record = {
                "identifier": 1,
                "name": "Emacs",
                "url": "https://ja.wikipedia.org/wiki/Emacs",
                "namespace": {"identifier": 0},
                "date_modified": "2026-06-01T00:00:00Z",
                "version": {"identifier": 1},
                "article_body": {"html": "<p>x</p>", "wikitext": "x"},
                "license": [],
                "redirects": [],
                "categories": [],
                "templates": [],
            }
            body = (json.dumps(record) + "\n").encode("utf-8")
            with tarfile.open(tar_path, mode="w:gz") as archive:
                info = tarfile.TarInfo(name="chunk_0.ndjson")
                info.size = len(body)
                archive.addfile(info, io.BytesIO(body))
            config = temporary / "ingest.toml"
            config.write_text(
                f'[paths]\nsources = "{sources}"\nwork = "{work}"\n', encoding="utf-8"
            )

            register_result = self.run_cli(
                "register-local-source",
                "--config",
                str(config),
                "--namespace",
                "0",
                "--snapshot-identifier",
                "jawiki_namespace_0",
                "--snapshot-version",
                "local-2026-07-14",
                "--date-modified",
                "2026-07-14T00:00:00Z",
                "--file",
                f"{tar_path}:jawiki_namespace_0_chunk_0",
                "--git-commit",
                "abc1234",
            )
            self.assertEqual(register_result.returncode, 0, register_result.stderr)
            lock_path = register_result.stdout.strip()

            ingest_result = self.run_cli(
                "ingest",
                "--config",
                str(config),
                "--lock-path",
                lock_path,
                "--git-commit",
                "abc1234",
                "--run-id",
                "test-run",
            )

            self.assertEqual(ingest_result.returncode, 0, ingest_result.stderr)
            manifest_path = Path(ingest_result.stdout.strip())
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(manifest["metrics"]["records_read"], 1)
            self.assertEqual(manifest["metrics"]["records_written"], 1)
            self.assertTrue((work / "raw.sqlite3").is_file())

            verify_result = self.run_cli("verify-raw", "--raw-database", str(work / "raw.sqlite3"))
            self.assertEqual(verify_result.returncode, 0, verify_result.stderr)
            verification = json.loads(verify_result.stdout)
            self.assertTrue(verification["ok"])
            self.assertEqual(verification["counts"]["accepted_articles"], 1)

    def test_verify_raw_help(self) -> None:
        result = self.run_cli("verify-raw", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--raw-database", result.stdout)
        self.assertIn("--sample-size", result.stdout)

    def test_normalize_help(self) -> None:
        result = self.run_cli("normalize", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--raw-database", result.stdout)
        self.assertIn("--model-database", result.stdout)
        self.assertIn("--force", result.stdout)

    def test_normalize_writes_manifest_and_model_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            sources = temporary / "sources"
            work = temporary / "work"
            tar_path = temporary / "downloads" / "chunk_0.tar.gz"
            tar_path.parent.mkdir(parents=True)
            record = {
                "identifier": 1,
                "name": "Emacs",
                "url": "https://ja.wikipedia.org/wiki/Emacs",
                "namespace": {"identifier": 0},
                "date_modified": "2026-06-01T00:00:00Z",
                "version": {"identifier": 1},
                "article_body": {"html": "<p>x</p>", "wikitext": "x"},
                "license": [],
                "redirects": [],
                "categories": [],
                "templates": [],
            }
            body = (json.dumps(record) + "\n").encode("utf-8")
            with tarfile.open(tar_path, mode="w:gz") as archive:
                info = tarfile.TarInfo(name="chunk_0.ndjson")
                info.size = len(body)
                archive.addfile(info, io.BytesIO(body))
            config = temporary / "normalize.toml"
            config.write_text(
                f'[paths]\nsources = "{sources}"\nwork = "{work}"\n', encoding="utf-8"
            )

            register_result = self.run_cli(
                "register-local-source",
                "--config",
                str(config),
                "--namespace",
                "0",
                "--snapshot-identifier",
                "jawiki_namespace_0",
                "--snapshot-version",
                "local-2026-07-14",
                "--date-modified",
                "2026-07-14T00:00:00Z",
                "--file",
                f"{tar_path}:jawiki_namespace_0_chunk_0",
                "--git-commit",
                "abc1234",
            )
            self.assertEqual(register_result.returncode, 0, register_result.stderr)
            lock_path = register_result.stdout.strip()

            ingest_result = self.run_cli(
                "ingest",
                "--config",
                str(config),
                "--lock-path",
                lock_path,
                "--git-commit",
                "abc1234",
                "--run-id",
                "test-run",
            )
            self.assertEqual(ingest_result.returncode, 0, ingest_result.stderr)

            normalize_result = self.run_cli(
                "normalize",
                "--config",
                str(config),
                "--git-commit",
                "abc1234",
                "--run-id",
                "test-run",
            )

            self.assertEqual(normalize_result.returncode, 0, normalize_result.stderr)
            manifest_path = Path(normalize_result.stdout.strip())
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(manifest["metrics"]["articles_read"], 1)
            self.assertTrue((work / "model.sqlite3").is_file())

    def test_generate_help(self) -> None:
        result = self.run_cli("generate", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--model-database", result.stdout)
        self.assertIn("--entries-output", result.stdout)
        self.assertIn("--force", result.stdout)

    def test_generate_writes_entries_jsonl_from_model_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            sources = temporary / "sources"
            work = temporary / "work"
            tar_path = temporary / "downloads" / "chunk_0.tar.gz"
            tar_path.parent.mkdir(parents=True)
            record = {
                "identifier": 1,
                "name": "Emacs",
                "url": "https://ja.wikipedia.org/wiki/Emacs",
                "namespace": {"identifier": 0},
                "date_modified": "2026-06-01T00:00:00Z",
                "version": {"identifier": 1},
                "article_body": {"html": "<p>x</p>", "wikitext": "x"},
                "license": [],
                "redirects": [],
                "categories": [],
                "templates": [],
            }
            body = (json.dumps(record) + "\n").encode("utf-8")
            with tarfile.open(tar_path, mode="w:gz") as archive:
                info = tarfile.TarInfo(name="chunk_0.ndjson")
                info.size = len(body)
                archive.addfile(info, io.BytesIO(body))
            config = temporary / "generate.toml"
            config.write_text(
                f'[paths]\nsources = "{sources}"\nwork = "{work}"\n', encoding="utf-8"
            )

            register_result = self.run_cli(
                "register-local-source",
                "--config",
                str(config),
                "--namespace",
                "0",
                "--snapshot-identifier",
                "jawiki_namespace_0",
                "--snapshot-version",
                "local-2026-07-14",
                "--date-modified",
                "2026-07-14T00:00:00Z",
                "--file",
                f"{tar_path}:jawiki_namespace_0_chunk_0",
                "--git-commit",
                "abc1234",
            )
            self.assertEqual(register_result.returncode, 0, register_result.stderr)
            lock_path = register_result.stdout.strip()

            ingest_result = self.run_cli(
                "ingest",
                "--config",
                str(config),
                "--lock-path",
                lock_path,
                "--git-commit",
                "abc1234",
                "--run-id",
                "test-run",
            )
            self.assertEqual(ingest_result.returncode, 0, ingest_result.stderr)

            normalize_result = self.run_cli(
                "normalize",
                "--config",
                str(config),
                "--git-commit",
                "abc1234",
                "--run-id",
                "test-run",
            )
            self.assertEqual(normalize_result.returncode, 0, normalize_result.stderr)

            entries_output = temporary / "entries.jsonl"
            generate_result = self.run_cli(
                "generate",
                "--config",
                str(config),
                "--entries-output",
                str(entries_output),
                "--git-commit",
                "abc1234",
                "--run-id",
                "test-run",
            )

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            manifest_path = Path(generate_result.stdout.strip())
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "complete")
            self.assertTrue(entries_output.is_file())
            lines = entries_output.read_text(encoding="utf-8").splitlines()
            self.assertGreaterEqual(len(lines), 1)
            record_out = json.loads(lines[0])
            self.assertEqual(record_out["tag"], "p1")

            verify_result = self.run_cli("verify", "--entries", str(entries_output))
            self.assertEqual(verify_result.returncode, 0, verify_result.stderr)
            verification = json.loads(verify_result.stdout)
            self.assertTrue(verification["ok"])
            self.assertEqual(verification["entry_count"], 1)

    def test_build_help(self) -> None:
        result = self.run_cli("build", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--lock-path", result.stdout)
        self.assertIn("--from-stage", result.stdout)
        self.assertIn("--force-stage", result.stdout)

    def _register_and_lock(self, temporary: Path, config: Path) -> str:
        tar_path = temporary / "downloads" / "chunk_0.tar.gz"
        tar_path.parent.mkdir(parents=True)
        record = {
            "identifier": 1,
            "name": "Emacs",
            "url": "https://ja.wikipedia.org/wiki/Emacs",
            "namespace": {"identifier": 0},
            "date_modified": "2026-06-01T00:00:00Z",
            "version": {"identifier": 1},
            "article_body": {"html": "<p>x</p>", "wikitext": "x"},
            "license": [],
            "redirects": [],
            "categories": [],
            "templates": [],
        }
        body = (json.dumps(record) + "\n").encode("utf-8")
        with tarfile.open(tar_path, mode="w:gz") as archive:
            info = tarfile.TarInfo(name="chunk_0.ndjson")
            info.size = len(body)
            archive.addfile(info, io.BytesIO(body))

        register_result = self.run_cli(
            "register-local-source",
            "--config",
            str(config),
            "--namespace",
            "0",
            "--snapshot-identifier",
            "jawiki_namespace_0",
            "--snapshot-version",
            "local-2026-07-14",
            "--date-modified",
            "2026-07-14T00:00:00Z",
            "--file",
            f"{tar_path}:jawiki_namespace_0_chunk_0",
            "--git-commit",
            "abc1234",
        )
        self.assertEqual(register_result.returncode, 0, register_result.stderr)
        return register_result.stdout.strip()

    def test_build_runs_all_stages_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            sources = temporary / "sources"
            work = temporary / "work"
            output = temporary / "output"
            config = temporary / "build.toml"
            config.write_text(
                f'[paths]\nsources = "{sources}"\nwork = "{work}"\noutput = "{output}"\n',
                encoding="utf-8",
            )
            lock_path = self._register_and_lock(temporary, config)

            build_result = self.run_cli(
                "build",
                "--config",
                str(config),
                "--lock-path",
                lock_path,
                "--git-commit",
                "abc1234",
                "--run-id",
                "test-build",
            )

            self.assertEqual(build_result.returncode, 0, build_result.stderr)
            manifest_paths = [Path(line) for line in build_result.stdout.splitlines()]
            self.assertEqual(len(manifest_paths), 3)
            for manifest_path in manifest_paths:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(manifest["status"], "complete")
            entries_path = output / "entries.jsonl"
            self.assertTrue(entries_path.is_file())

    def test_build_resumes_completed_stages_on_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            sources = temporary / "sources"
            work = temporary / "work"
            output = temporary / "output"
            config = temporary / "build.toml"
            config.write_text(
                f'[paths]\nsources = "{sources}"\nwork = "{work}"\noutput = "{output}"\n',
                encoding="utf-8",
            )
            lock_path = self._register_and_lock(temporary, config)

            first = self.run_cli(
                "build",
                "--config",
                str(config),
                "--lock-path",
                lock_path,
                "--git-commit",
                "abc1234",
                "--run-id",
                "same-run",
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            first_started_at = {
                str(manifest_path): json.loads(manifest_path.read_text(encoding="utf-8"))[
                    "started_at"
                ]
                for manifest_path in (Path(line) for line in first.stdout.splitlines())
            }

            second = self.run_cli(
                "build",
                "--config",
                str(config),
                "--lock-path",
                lock_path,
                "--git-commit",
                "abc1234",
                "--run-id",
                "same-run",
            )
            self.assertEqual(second.returncode, 0, second.stderr)

            for manifest_path in (Path(line) for line in second.stdout.splitlines()):
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(manifest["status"], "complete")
                # unchanged started_at proves the stage was skipped, not rerun.
                self.assertEqual(manifest["started_at"], first_started_at[str(manifest_path)])

    def test_build_from_stage_skips_earlier_stages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            sources = temporary / "sources"
            work = temporary / "work"
            output = temporary / "output"
            config = temporary / "build.toml"
            config.write_text(
                f'[paths]\nsources = "{sources}"\nwork = "{work}"\noutput = "{output}"\n',
                encoding="utf-8",
            )
            lock_path = self._register_and_lock(temporary, config)

            first = self.run_cli(
                "build",
                "--config",
                str(config),
                "--lock-path",
                lock_path,
                "--git-commit",
                "abc1234",
                "--run-id",
                "first-run",
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            second = self.run_cli(
                "build",
                "--config",
                str(config),
                "--lock-path",
                lock_path,
                "--git-commit",
                "abc1234",
                "--run-id",
                "second-run",
                "--from-stage",
                "generate",
            )

            self.assertEqual(second.returncode, 0, second.stderr)
            manifest_paths = [Path(line) for line in second.stdout.splitlines()]
            self.assertEqual(len(manifest_paths), 1)
            self.assertIn("50-generate.json", str(manifest_paths[0]))

    def test_verify_help(self) -> None:
        result = self.run_cli("verify", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--entries", result.stdout)

    def test_verify_reports_issues_and_nonzero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            entries_path = Path(directory) / "entries.jsonl"
            entries_path.write_text(
                json.dumps(
                    {"tag": "p1", "title": "A", "aliases": [], "body": "", "targets": ["pmissing"]}
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_cli("verify", "--entries", str(entries_path))

            self.assertEqual(result.returncode, 1)
            report = json.loads(result.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any(issue["code"] == "UNKNOWN_TARGET" for issue in report["issues"]))

    def test_image_plan_help(self) -> None:
        result = self.run_cli("image-plan", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--model-database", result.stdout)

    def test_image_fetch_help(self) -> None:
        result = self.run_cli("image-fetch", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--originals-dir", result.stdout)

    def test_image_convert_help(self) -> None:
        result = self.run_cli("image-convert", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--graphics-dir", result.stdout)

    def test_image_plan_lists_media_from_model_database(self) -> None:
        from datetime import UTC, datetime

        from wikiepwing.model.article import Article, MediaReference
        from wikiepwing.model.canonical import encode_article
        from wikiepwing.model.database import connect_model_database, initialize_model_database
        from wikiepwing.model.logical_hash import compute_logical_hash
        from wikiepwing.model.repository import ModelRepository

        with tempfile.TemporaryDirectory() as directory:
            model_database_path = Path(directory) / "model.sqlite3"
            migrations = Path(__file__).parents[1] / "migrations" / "model"
            initialize_model_database(model_database_path, migrations)

            article = Article(
                page_id=1,
                revision_id=100,
                title="Emacs",
                normalized_title="Emacs",
                source_url="https://ja.wikipedia.org/wiki/Emacs",
                source_date_modified=datetime(2026, 1, 1, tzinfo=UTC),
                abstract=None,
                blocks=(),
                aliases=(),
                categories=(),
                media=(
                    MediaReference(
                        media_id="https://upload.wikimedia.org/a.png",
                        source_url="https://upload.wikimedia.org/a.png",
                        source_name="a.png",
                        alt_text=None,
                        caption=None,
                        role="main",
                        source_width=100,
                        source_height=100,
                    ),
                ),
                diagnostics=(),
                source_license_ids=(),
            )
            with connect_model_database(model_database_path) as connection:
                repository = ModelRepository(connection)
                with repository.batch():
                    repository.write_article(
                        article,
                        canonical_json=encode_article(article),
                        logical_hash=compute_logical_hash(article),
                        normalize_status="complete",
                    )

            result = self.run_cli("image-plan", "--model-database", str(model_database_path))

            self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads(result.stdout)
            self.assertEqual(len(plan), 1)
            self.assertEqual(plan[0]["page_id"], 1)
            self.assertEqual(plan[0]["source_url"], "https://upload.wikimedia.org/a.png")

    def test_image_plan_empty_database_lists_no_media(self) -> None:
        from wikiepwing.model.database import initialize_model_database

        with tempfile.TemporaryDirectory() as directory:
            model_database_path = Path(directory) / "model.sqlite3"
            migrations = Path(__file__).parents[1] / "migrations" / "model"
            initialize_model_database(model_database_path, migrations)

            result = self.run_cli("image-plan", "--model-database", str(model_database_path))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), [])


if __name__ == "__main__":
    unittest.main()
