from pathlib import Path

from wikiepwing.doctor import doctor_payload, run_doctor


def _write_config(config_path: Path) -> None:
    root = config_path.parent
    contents = "\n".join(
        [
            "[build]",
            "schema_version = 1",
            'project = "jawiki"',
            'profile = "minimal"',
            "",
            "[paths]",
            f'data_dir = "{root / "data"}"',
            f'output_dir = "{root / "output"}"',
            f'reports_dir = "{root / "reports"}"',
            "",
            "[runtime]",
            'log_level = "INFO"',
            "",
        ]
    )
    config_path.write_text(contents, encoding="utf-8")


def test_doctor_reports_configured_directories(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    _write_config(config_path)

    payload = doctor_payload(run_doctor(config_path))

    assert payload["ok"]
    assert len(payload["checks"]) == 5
