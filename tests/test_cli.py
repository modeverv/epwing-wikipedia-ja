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


if __name__ == "__main__":
    unittest.main()
