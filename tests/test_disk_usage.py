from __future__ import annotations

from pathlib import Path

from wikiepwing.config import AppConfig, PathsConfig
from wikiepwing.disk_usage import compute_disk_usage


def _config(tmp_path: Path, **overrides: Path) -> AppConfig:
    paths = PathsConfig(
        sources=overrides.get("sources", tmp_path / "sources"),
        reference=overrides.get("reference", tmp_path / "reference"),
        work=overrides.get("work", tmp_path / "work"),
        cache=overrides.get("cache", tmp_path / "cache"),
        output=overrides.get("output", tmp_path / "output"),
        reports=overrides.get("reports", tmp_path / "reports"),
        logs=overrides.get("logs", tmp_path / "logs"),
    )
    return AppConfig(
        schema_version=1,
        project="jawiki",
        profile="lite",
        paths=paths,
        source_files=(),
        _values={},
    )


def test_missing_directories_report_zero_size(tmp_path: Path) -> None:
    report = compute_disk_usage(_config(tmp_path))

    assert all(not usage.exists for usage in report.paths)
    assert all(usage.size_bytes == 0 for usage in report.paths)
    assert report.total_bytes == 0


def test_existing_directory_reports_its_size(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    (work / "raw.sqlite3").write_bytes(b"x" * 100)

    report = compute_disk_usage(_config(tmp_path, work=work))

    work_usage = next(usage for usage in report.paths if usage.name == "work")
    assert work_usage.exists is True
    assert work_usage.size_bytes == 100


def test_directory_size_is_recursive(tmp_path: Path) -> None:
    work = tmp_path / "work"
    nested = work / "runs" / "run1"
    nested.mkdir(parents=True)
    (nested / "manifest.json").write_bytes(b"y" * 50)

    report = compute_disk_usage(_config(tmp_path, work=work))

    work_usage = next(usage for usage in report.paths if usage.name == "work")
    assert work_usage.size_bytes == 50


def test_symlinks_are_not_double_counted(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    real_file = tmp_path / "real.bin"
    real_file.write_bytes(b"z" * 30)
    (work / "link.bin").symlink_to(real_file)

    report = compute_disk_usage(_config(tmp_path, work=work))

    work_usage = next(usage for usage in report.paths if usage.name == "work")
    assert work_usage.size_bytes == 0


def test_total_bytes_equals_sum_of_path_sizes(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    (work / "a.bin").write_bytes(b"1" * 10)
    output = tmp_path / "output"
    output.mkdir()
    (output / "b.bin").write_bytes(b"2" * 20)

    report = compute_disk_usage(_config(tmp_path, work=work, output=output))

    assert report.total_bytes == sum(usage.size_bytes for usage in report.paths)
    assert report.total_bytes == 30


def test_report_payload_is_json_serializable(tmp_path: Path) -> None:
    import json

    report = compute_disk_usage(_config(tmp_path))

    json.dumps(report.payload())


def test_free_bytes_is_nonnegative(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()

    report = compute_disk_usage(_config(tmp_path, work=work))

    assert report.free_bytes >= 0
