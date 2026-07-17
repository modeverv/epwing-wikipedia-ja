from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from wikiepwing.gaiji.capacity import limit_existing_artifacts


def test_limits_existing_artifacts_by_frequency_and_rewrites_overflow(tmp_path: Path) -> None:
    database = tmp_path / "gaiji.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE gaiji (assigned_code TEXT, sequence TEXT, width_class TEXT, "
        "usage_count INTEGER)"
    )
    connection.executemany(
        "INSERT INTO gaiji VALUES (?, ?, ?, ?)",
        [
            ("wide-0001", "丂", "wide", 1),
            ("wide-0002", "髙", "wide", 5),
            ("narrow-0001", "é", "narrow", 3),
        ],
    )
    connection.commit()
    connection.close()

    gaiji_source = tmp_path / "gaiji-source"
    gaiji_source.mkdir()
    (gaiji_source / "halfchars.txt").write_text("narrow-0001 narrow-0001.xbm\n", encoding="ascii")
    (gaiji_source / "fullchars.txt").write_text(
        "wide-0001 wide-0001.xbm\nwide-0002 wide-0002.xbm\n", encoding="ascii"
    )
    for code in ("narrow-0001", "wide-0001", "wide-0002"):
        (gaiji_source / f"{code}.xbm").write_bytes(code.encode("ascii"))

    entries_source = tmp_path / "source.jsonl"
    entries_source.write_text(
        json.dumps({"body": "@@GAIJI:wide-0001@@@@GAIJI:wide-0002@@@@GAIJI:narrow-0001@@"}) + "\n",
        encoding="utf-8",
    )
    entries_output = tmp_path / "limited.jsonl"
    gaiji_output = tmp_path / "gaiji-output"
    report = tmp_path / "report.json"

    metrics = limit_existing_artifacts(
        entries_source=entries_source,
        database_path=database,
        gaiji_source=gaiji_source,
        entries_destination=entries_output,
        gaiji_destination=gaiji_output,
        report_path=report,
        max_per_width=1,
    )

    body = json.loads(entries_output.read_text(encoding="utf-8"))["body"]
    assert body == "[U+4E02]@@GAIJI:wide-0002@@@@GAIJI:narrow-0001@@"
    assert metrics.selected_tokens == 2
    assert metrics.overflow_tokens == 1
    assert (gaiji_output / "wide-0002.xbm").is_file()
    assert not (gaiji_output / "wide-0001.xbm").exists()
    assert report.is_file()
