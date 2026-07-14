from __future__ import annotations

import json
import subprocess
import sys
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


if __name__ == "__main__":
    unittest.main()
