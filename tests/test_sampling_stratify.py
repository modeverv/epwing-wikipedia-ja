from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from wikiepwing.ingest.record_parser import RawArticle, SourceImage
from wikiepwing.sampling.stratify import (
    build_stratified_sample_ndjson,
    compute_signals,
    select_stratified_sample,
    write_sample_report,
)


def _article(**overrides: object) -> RawArticle:
    defaults: dict[str, object] = {
        "page_id": 1,
        "revision_id": 1,
        "title": "Emacs",
        "namespace_id": 0,
        "url": "https://ja.wikipedia.org/wiki/Emacs",
        "date_modified": datetime(2026, 1, 1, tzinfo=UTC),
        "html": "<p>short</p>",
        "wikitext": None,
        "redirects": (),
        "categories": (),
        "templates": (),
        "licenses": (),
        "main_image": None,
        "source_sequence": 0,
        "source_hash": "hash",
    }
    defaults.update(overrides)
    return RawArticle(**defaults)  # type: ignore[arg-type]


def test_baseline_when_nothing_matches() -> None:
    signals = compute_signals(_article())

    assert signals.strata == ("baseline",)


def test_long_article_stratum() -> None:
    signals = compute_signals(_article(html="<p>" + "x" * 100_000 + "</p>"))

    assert "long_article" in signals.strata


def test_table_heavy_stratum() -> None:
    html = "<table></table>" * 3
    signals = compute_signals(_article(html=html))

    assert "table_heavy" in signals.strata


def test_table_heavy_requires_minimum_count() -> None:
    html = "<table></table>" * 2
    signals = compute_signals(_article(html=html))

    assert "table_heavy" not in signals.strata


def test_image_heavy_stratum() -> None:
    signals = compute_signals(
        _article(main_image=SourceImage(content_url="https://x/y.png", width=100, height=100))
    )

    assert "image_heavy" in signals.strata


def test_math_heavy_stratum() -> None:
    signals = compute_signals(_article(html='<math alttext="x"></math>'))

    assert "math_heavy" in signals.strata


def test_disambiguation_stratum() -> None:
    signals = compute_signals(_article(categories=("Category:曖昧さ回避",)))

    assert "disambiguation" in signals.strata


def test_list_article_stratum() -> None:
    signals = compute_signals(_article(title="日本の都市の一覧"))

    assert "list_article" in signals.strata


def test_history_or_literature_stratum() -> None:
    signals = compute_signals(_article(categories=("Category:日本の歴史",)))

    assert "history_or_literature" in signals.strata


def test_technical_stratum() -> None:
    signals = compute_signals(_article(categories=("Category:コンピュータ技術",)))

    assert "technical" in signals.strata


def test_rare_unicode_stratum() -> None:
    signals = compute_signals(_article(title="\U00020000"))

    assert "rare_unicode" in signals.strata


def test_common_kanji_title_is_not_rare_unicode() -> None:
    signals = compute_signals(_article(title="日本語"))

    assert "rare_unicode" not in signals.strata


def test_article_can_match_multiple_strata() -> None:
    signals = compute_signals(
        _article(
            html="<table></table>" * 3,
            categories=("Category:日本の歴史",),
        )
    )

    assert "table_heavy" in signals.strata
    assert "history_or_literature" in signals.strata


def test_select_stratified_sample_fills_from_non_baseline_first() -> None:
    articles = [
        _article(page_id=1, main_image=SourceImage(content_url="u", width=1, height=1)),
        _article(page_id=2),
        _article(page_id=3),
    ]

    sample = select_stratified_sample(articles, target_total=2, min_per_stratum=1)

    assert 1 in sample.selected_page_ids
    assert len(sample.selected_page_ids) == 2


def test_select_stratified_sample_respects_target_total() -> None:
    articles = [_article(page_id=i) for i in range(10)]

    sample = select_stratified_sample(articles, target_total=3, min_per_stratum=1)

    assert len(sample.selected_page_ids) == 3
    assert sample.total_scanned == 10


def test_select_stratified_sample_deduplicates_across_strata() -> None:
    articles = [
        _article(
            page_id=1,
            html="<table></table>" * 3,
            categories=("Category:日本の歴史",),
        )
    ]

    sample = select_stratified_sample(articles, target_total=10, min_per_stratum=5)

    assert sample.selected_page_ids == (1,)
    assert sample.stratum_selected_counts["table_heavy"] == 1
    assert sample.stratum_selected_counts["history_or_literature"] == 1


def test_select_stratified_sample_empty_input() -> None:
    sample = select_stratified_sample([], target_total=10, min_per_stratum=1)

    assert sample.total_scanned == 0
    assert sample.selected_page_ids == ()


def _write_ndjson(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def _record(page_id: int, title: str, **overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "identifier": page_id,
        "name": title,
        "url": f"https://ja.wikipedia.org/wiki/{title}",
        "namespace": {"identifier": 0},
        "date_modified": "2026-01-01T00:00:00Z",
        "version": {"identifier": page_id * 10},
        "article_body": {"html": "<p>text</p>"},
    }
    record.update(overrides)
    return record


def test_build_stratified_sample_ndjson_writes_selected_lines(tmp_path: Path) -> None:
    source = tmp_path / "source.ndjson"
    _write_ndjson(
        source,
        [
            _record(1, "Emacs"),
            _record(2, "Vim"),
            _record(3, "Linux"),
        ],
    )
    output = tmp_path / "sample.ndjson"

    sample = build_stratified_sample_ndjson(source, output, target_total=2, min_per_stratum=1)

    assert output.is_file()
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    written_ids = {json.loads(line)["identifier"] for line in lines}
    assert written_ids == set(sample.selected_page_ids)


def test_build_stratified_sample_ndjson_creates_missing_directory(tmp_path: Path) -> None:
    source = tmp_path / "source.ndjson"
    _write_ndjson(source, [_record(1, "Emacs")])
    output = tmp_path / "nested" / "sample.ndjson"

    build_stratified_sample_ndjson(source, output, target_total=1, min_per_stratum=1)

    assert output.is_file()


def test_write_sample_report_contains_expected_fields(tmp_path: Path) -> None:
    source = tmp_path / "source.ndjson"
    _write_ndjson(source, [_record(1, "Emacs"), _record(2, "Vim")])
    output = tmp_path / "sample.ndjson"
    sample = build_stratified_sample_ndjson(source, output, target_total=2, min_per_stratum=1)

    report_path = tmp_path / "report.json"
    write_sample_report(sample, report_path)

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["total_scanned"] == 2
    assert payload["total_selected"] == 2
    assert "baseline" in payload["stratum_found_counts"]
    assert "baseline" in payload["stratum_selected_counts"]
