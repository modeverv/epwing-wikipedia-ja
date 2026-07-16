"""Stratified sample selection (TASK-R001, PLAN.md Phase 20's "10,000記事耐久試験").

Before attempting any full-corpus build, Phase 20 calls for a sample
that covers more than a bare page-ID range: long articles, table-heavy,
image-heavy, math-heavy, Japanese history/literature, technical,
disambiguation, list articles, and rare Unicode. `compute_signals`
classifies one already-parsed `RawArticle` (TASK-A-era
`ingest.record_parser.parse_record`, reused here rather than
re-implementing NDJSON parsing) into zero or more of those strata (or
`"baseline"` if none match); `select_stratified_sample` streams a whole
NDJSON source once, keeping up to `min_per_stratum` articles per
non-baseline stratum before filling the remaining budget with baseline
articles, so a multi-gigabyte source file is never held in memory.

Every heuristic here (table/math tag counting, disambiguation/history/
literature/technical category keyword matching, rare-Unicode codepoint
ranges) is an approximation, not a guarantee of precise classification --
good enough to build a diverse endurance-test sample, not a claim about
any single article's true nature.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from wikiepwing.ingest.record_parser import RawArticle, parse_record
from wikiepwing.pipeline.atomic_write import atomic_write_text

Stratum = Literal[
    "long_article",
    "table_heavy",
    "image_heavy",
    "math_heavy",
    "disambiguation",
    "list_article",
    "history_or_literature",
    "technical",
    "rare_unicode",
    "baseline",
]

_NON_BASELINE_STRATA: tuple[Stratum, ...] = (
    "long_article",
    "table_heavy",
    "image_heavy",
    "math_heavy",
    "disambiguation",
    "list_article",
    "history_or_literature",
    "technical",
    "rare_unicode",
)
_ALL_STRATA: tuple[Stratum, ...] = (*_NON_BASELINE_STRATA, "baseline")

_LONG_ARTICLE_MIN_HTML_UTF8_BYTES = 100_000
_TABLE_HEAVY_MIN_TABLE_COUNT = 3
_TABLE_TAG = re.compile(r"<table\b", re.IGNORECASE)
_MATH_TAG = re.compile(r"<math\b", re.IGNORECASE)
_DISAMBIGUATION_CATEGORY = re.compile(r"曖昧さ回避")
_LIST_TITLE = re.compile(r"の一覧$|^List of ", re.IGNORECASE)
_HISTORY_OR_LITERATURE_CATEGORY = re.compile(r"歴史|文学")
_TECHNICAL_CATEGORY = re.compile(r"技術|工学|コンピュータ|情報科学")
_RARE_UNICODE_CATEGORIES = frozenset({"Co", "Cn"})


@dataclass(frozen=True, slots=True)
class ArticleSignals:
    """The stratum classification for one article."""

    page_id: int
    title: str
    strata: tuple[Stratum, ...]


def compute_signals(article: RawArticle) -> ArticleSignals:
    """Classify `article` into every matching stratum, or `("baseline",)` if none match."""
    html = article.html or ""
    strata: list[Stratum] = []

    if len(html.encode("utf-8")) >= _LONG_ARTICLE_MIN_HTML_UTF8_BYTES:
        strata.append("long_article")
    if len(_TABLE_TAG.findall(html)) >= _TABLE_HEAVY_MIN_TABLE_COUNT:
        strata.append("table_heavy")
    if article.main_image is not None:
        strata.append("image_heavy")
    if _MATH_TAG.search(html):
        strata.append("math_heavy")
    if any(_DISAMBIGUATION_CATEGORY.search(category) for category in article.categories):
        strata.append("disambiguation")
    if _LIST_TITLE.search(article.title):
        strata.append("list_article")
    if any(_HISTORY_OR_LITERATURE_CATEGORY.search(category) for category in article.categories):
        strata.append("history_or_literature")
    if any(_TECHNICAL_CATEGORY.search(category) for category in article.categories):
        strata.append("technical")
    if _has_rare_unicode(article.title) or _has_rare_unicode(html):
        strata.append("rare_unicode")

    if not strata:
        strata.append("baseline")
    return ArticleSignals(page_id=article.page_id, title=article.title, strata=tuple(strata))


def _has_rare_unicode(text: str) -> bool:
    for character in text:
        codepoint = ord(character)
        if 0x3400 <= codepoint <= 0x4DBF or codepoint >= 0x20000:
            return True
        if unicodedata.category(character) in _RARE_UNICODE_CATEGORIES:
            return True
    return False


@dataclass(frozen=True, slots=True)
class StratifiedSample:
    """The outcome of one streaming stratified-selection pass."""

    total_scanned: int
    selected_page_ids: tuple[int, ...]
    stratum_found_counts: dict[Stratum, int]
    stratum_selected_counts: dict[Stratum, int]


def select_stratified_sample(
    articles: Iterable[RawArticle],
    *,
    target_total: int,
    min_per_stratum: int,
) -> StratifiedSample:
    """Select up to `target_total` articles, streaming `articles` in a single pass.

    Each non-baseline stratum gets up to `min_per_stratum` articles
    (first-seen, so the result is deterministic for a fixed input order);
    the remaining budget up to `target_total` is filled with baseline
    articles. An article matching more than one stratum is only selected
    once but still counts toward every stratum it matches.
    """
    if target_total < 0:
        raise ValueError("target_total must not be negative")
    if min_per_stratum < 0:
        raise ValueError("min_per_stratum must not be negative")

    selected_page_ids: list[int] = []
    selected_ids: set[int] = set()
    baseline_candidates: list[int] = []
    stratum_found_counts: dict[Stratum, int] = dict.fromkeys(_ALL_STRATA, 0)
    stratum_selected_counts: dict[Stratum, int] = dict.fromkeys(_ALL_STRATA, 0)
    total_scanned = 0

    for article in articles:
        total_scanned += 1
        signals = compute_signals(article)
        for stratum in signals.strata:
            stratum_found_counts[stratum] += 1

        if article.page_id in selected_ids:
            continue

        wants_stratum = any(
            stratum != "baseline" and stratum_selected_counts[stratum] < min_per_stratum
            for stratum in signals.strata
        )
        if wants_stratum and len(selected_page_ids) < target_total:
            selected_page_ids.append(article.page_id)
            selected_ids.add(article.page_id)
            for stratum in signals.strata:
                stratum_selected_counts[stratum] += 1
        elif "baseline" in signals.strata:
            baseline_candidates.append(article.page_id)

    remaining = target_total - len(selected_page_ids)
    for page_id in baseline_candidates[: max(remaining, 0)]:
        selected_page_ids.append(page_id)
        stratum_selected_counts["baseline"] += 1

    return StratifiedSample(
        total_scanned=total_scanned,
        selected_page_ids=tuple(selected_page_ids),
        stratum_found_counts=stratum_found_counts,
        stratum_selected_counts=stratum_selected_counts,
    )


def iter_raw_articles(ndjson_path: Path) -> Iterator[tuple[bytes, RawArticle]]:
    """Stream `(raw_line, parsed_article)` pairs from an NDJSON file, one line at a time."""
    with ndjson_path.open("rb") as source:
        for index, raw_line in enumerate(source):
            line = raw_line.rstrip(b"\n")
            if not line:
                continue
            yield line, parse_record(line, source_sequence=index)


def build_stratified_sample_ndjson(
    source_ndjson: Path,
    output_ndjson: Path,
    *,
    target_total: int,
    min_per_stratum: int,
) -> StratifiedSample:
    """Select a stratified sample from `source_ndjson` and write its raw lines to `output_ndjson`.

    Reads `source_ndjson` twice (selection, then extraction) rather than
    buffering every candidate line in memory -- acceptable for a
    multi-gigabyte source since each pass is a single sequential read.
    """
    sample = select_stratified_sample(
        (article for _line, article in iter_raw_articles(source_ndjson)),
        target_total=target_total,
        min_per_stratum=min_per_stratum,
    )
    selected_ids = set(sample.selected_page_ids)

    output_ndjson.parent.mkdir(parents=True, exist_ok=True)
    with output_ndjson.open("wb") as destination:
        for line, article in iter_raw_articles(source_ndjson):
            if article.page_id in selected_ids:
                destination.write(line + b"\n")

    return sample


def write_sample_report(sample: StratifiedSample, output_path: Path) -> None:
    """Write `sample`'s stratum coverage as a JSON report, atomically."""
    payload = {
        "schema_version": 1,
        "total_scanned": sample.total_scanned,
        "total_selected": len(sample.selected_page_ids),
        "stratum_found_counts": dict(sample.stratum_found_counts),
        "stratum_selected_counts": dict(sample.stratum_selected_counts),
    }
    atomic_write_text(
        output_path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
