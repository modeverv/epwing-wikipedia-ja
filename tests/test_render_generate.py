from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.model.article import Article
from wikiepwing.model.blocks import ParagraphBlock
from wikiepwing.model.canonical import encode_article
from wikiepwing.model.database import connect_model_database, initialize_model_database
from wikiepwing.model.inline import TextInline
from wikiepwing.model.logical_hash import compute_logical_hash
from wikiepwing.model.repository import ModelRepository
from wikiepwing.render.generate import GenerateError, read_manifest_status, run_generate

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "model"


def _make_article(**overrides: object) -> Article:
    defaults: dict[str, object] = {
        "page_id": 1,
        "revision_id": 100,
        "title": "Emacs",
        "normalized_title": "Emacs",
        "source_url": "https://ja.wikipedia.org/wiki/Emacs",
        "source_date_modified": datetime(2026, 6, 1, tzinfo=UTC),
        "abstract": "An editor.",
        "blocks": (ParagraphBlock(inlines=(TextInline(value="Body text."),)),),
        "aliases": (),
        "categories": (),
        "media": (),
        "diagnostics": (),
        "source_license_ids": (),
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def _seed_model_database(database_path: Path, articles: list[tuple[Article, str]]) -> Path:
    database = initialize_model_database(database_path, MIGRATIONS)
    with connect_model_database(database) as connection:
        repository = ModelRepository(connection)
        with repository.batch():
            for article, status in articles:
                repository.write_article(
                    article,
                    canonical_json=encode_article(article),
                    logical_hash=compute_logical_hash(article),
                    normalize_status=status,
                )
    return database


def test_run_generate_writes_entries_for_non_rejected_articles(tmp_path: Path) -> None:
    database_path = _seed_model_database(
        tmp_path / "model.sqlite3",
        [
            (_make_article(page_id=1, title="Emacs"), "complete"),
            (_make_article(page_id=2, title="Linux"), "fallback"),
            (_make_article(page_id=3, title="Bad"), "rejected"),
        ],
    )

    result = run_generate(
        model_database_path=database_path,
        entries_path=tmp_path / "entries.jsonl",
        manifest_path=tmp_path / "manifests" / "50-generate.json",
        run_id="test-run",
    )

    assert result.manifest.status == "complete"
    assert result.manifest.metrics.articles_read == 3
    assert result.manifest.metrics.entries_written == 2
    assert result.manifest.metrics.articles_skipped == 1

    lines = result.entries_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    tags = {json.loads(line)["tag"] for line in lines}
    assert tags == {"p1", "p2"}


def test_run_generate_refuses_running_manifest_without_force(tmp_path: Path) -> None:
    database_path = _seed_model_database(
        tmp_path / "model.sqlite3", [(_make_article(), "complete")]
    )
    manifest_path = tmp_path / "manifests" / "50-generate.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text('{"status": "running"}', encoding="utf-8")

    with pytest.raises(GenerateError, match="still 'running'"):
        run_generate(
            model_database_path=database_path,
            entries_path=tmp_path / "entries.jsonl",
            manifest_path=manifest_path,
            run_id="test-run",
        )


def test_run_generate_force_proceeds_over_running_manifest(tmp_path: Path) -> None:
    database_path = _seed_model_database(
        tmp_path / "model.sqlite3", [(_make_article(), "complete")]
    )
    manifest_path = tmp_path / "manifests" / "50-generate.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text('{"status": "running"}', encoding="utf-8")

    result = run_generate(
        model_database_path=database_path,
        entries_path=tmp_path / "entries.jsonl",
        manifest_path=manifest_path,
        run_id="test-run",
        force=True,
    )

    assert result.manifest.status == "complete"


def test_run_generate_skips_rerun_when_previous_run_is_complete_and_unchanged(
    tmp_path: Path,
) -> None:
    database_path = _seed_model_database(
        tmp_path / "model.sqlite3", [(_make_article(), "complete")]
    )
    entries_path = tmp_path / "entries.jsonl"
    manifest_path = tmp_path / "manifests" / "50-generate.json"

    first = run_generate(
        model_database_path=database_path,
        entries_path=entries_path,
        manifest_path=manifest_path,
        run_id="first-run",
    )
    entries_text_after_first = entries_path.read_text(encoding="utf-8")

    second = run_generate(
        model_database_path=database_path,
        entries_path=entries_path,
        manifest_path=manifest_path,
        run_id="second-run",
    )

    assert second.manifest.run_id == first.manifest.run_id
    assert second.manifest.status == "complete"
    assert entries_path.read_text(encoding="utf-8") == entries_text_after_first


def test_run_generate_force_reruns_despite_complete_manifest(tmp_path: Path) -> None:
    database_path = _seed_model_database(
        tmp_path / "model.sqlite3", [(_make_article(), "complete")]
    )
    entries_path = tmp_path / "entries.jsonl"
    manifest_path = tmp_path / "manifests" / "50-generate.json"

    run_generate(
        model_database_path=database_path,
        entries_path=entries_path,
        manifest_path=manifest_path,
        run_id="first-run",
    )

    second = run_generate(
        model_database_path=database_path,
        entries_path=entries_path,
        manifest_path=manifest_path,
        run_id="second-run",
        force=True,
    )

    assert second.manifest.run_id == "second-run"


def test_read_manifest_status_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_manifest_status(tmp_path / "missing.json") is None
