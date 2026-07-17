from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest
from PIL import Image

from wikiepwing.media.cache import MediaCache
from wikiepwing.media.downloader import MediaDownloadError, MediaDownloadResult
from wikiepwing.media.orchestrate import (
    FetchOutcome,
    FetchProgress,
    MediaPlanEntry,
    convert_media,
    fetch_media,
    plan_media,
)
from wikiepwing.media.raster_converter import is_imagemagick_available
from wikiepwing.model.article import Article, MediaReference
from wikiepwing.model.canonical import encode_article
from wikiepwing.model.database import connect_model_database, initialize_model_database
from wikiepwing.model.logical_hash import compute_logical_hash
from wikiepwing.model.repository import ModelRepository

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "model"

_requires_imagemagick = pytest.mark.skipif(
    not is_imagemagick_available(),
    reason="ImageMagick (magick/convert) is not installed in this environment",
)


def _make_article(**overrides: object) -> Article:
    defaults: dict[str, object] = {
        "page_id": 1,
        "revision_id": 100,
        "title": "Emacs",
        "normalized_title": "Emacs",
        "source_url": "https://ja.wikipedia.org/wiki/Emacs",
        "source_date_modified": datetime(2026, 1, 1, tzinfo=UTC),
        "abstract": None,
        "blocks": (),
        "aliases": (),
        "categories": (),
        "media": (
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
        "diagnostics": (),
        "source_license_ids": (),
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def _write_article(database: Path, article: Article, *, normalize_status: str = "complete") -> None:
    with connect_model_database(database) as connection:
        repository = ModelRepository(connection)
        with repository.batch():
            repository.write_article(
                article,
                canonical_json=encode_article(article),
                logical_hash=compute_logical_hash(article),
                normalize_status=normalize_status,
            )


def test_plan_media_reads_media_references(tmp_path: Path) -> None:
    database = initialize_model_database(tmp_path / "model.sqlite3", MIGRATIONS)
    _write_article(database, _make_article())

    plan = plan_media(database)

    assert plan == (MediaPlanEntry(page_id=1, media=_make_article().media[0]),)


def test_plan_media_excludes_rejected_articles(tmp_path: Path) -> None:
    database = initialize_model_database(tmp_path / "model.sqlite3", MIGRATIONS)
    _write_article(database, _make_article(), normalize_status="rejected")

    plan = plan_media(database)

    assert plan == ()


def test_plan_media_empty_database(tmp_path: Path) -> None:
    database = initialize_model_database(tmp_path / "model.sqlite3", MIGRATIONS)

    assert plan_media(database) == ()


@dataclass
class _FakeDownloader:
    results_by_url: dict[str, MediaDownloadResult | Exception] = field(default_factory=dict)

    def download(self, url: str) -> MediaDownloadResult:
        result = self.results_by_url[url]
        if isinstance(result, Exception):
            raise result
        return result


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), (255, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


def _media(url: str) -> MediaReference:
    return MediaReference(
        media_id=url,
        source_url=url,
        source_name=None,
        alt_text=None,
        caption=None,
        role="body",
        source_width=None,
        source_height=None,
    )


def _fetch_outcome(
    url: str, content: bytes, *, content_hash: str, fmt: str = "png"
) -> FetchOutcome:
    return FetchOutcome(
        source_url=url, content=content, content_hash=content_hash, detected_format=fmt, error=None
    )


def test_fetch_media_downloads_each_unique_url_once() -> None:
    downloader = _FakeDownloader(
        results_by_url={
            "https://example.org/a.png": MediaDownloadResult(
                content=_png_bytes(), content_type="image/png"
            ),
        }
    )
    plan = (
        MediaPlanEntry(page_id=1, media=_media("https://example.org/a.png")),
        MediaPlanEntry(page_id=2, media=_media("https://example.org/a.png")),
    )

    outcomes = fetch_media(plan, downloader=downloader, max_pixels=10_000, allow_svg=True)  # type: ignore[arg-type]

    assert len(outcomes) == 1
    assert outcomes[0].ok is True


def test_fetch_media_records_download_failure() -> None:
    downloader = _FakeDownloader(
        results_by_url={"https://example.org/a.png": MediaDownloadError("boom")}
    )
    plan = (MediaPlanEntry(page_id=1, media=_media("https://example.org/a.png")),)

    outcomes = fetch_media(plan, downloader=downloader, max_pixels=10_000, allow_svg=True)  # type: ignore[arg-type]

    assert outcomes[0].ok is False
    assert outcomes[0].error is not None


def test_fetch_media_sanitizes_svg() -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>bad()</script><rect/></svg>'
    downloader = _FakeDownloader(
        results_by_url={
            "https://example.org/a.svg": MediaDownloadResult(
                content=svg, content_type="image/svg+xml"
            )
        }
    )
    plan = (MediaPlanEntry(page_id=1, media=_media("https://example.org/a.svg")),)

    outcomes = fetch_media(plan, downloader=downloader, max_pixels=10_000, allow_svg=True)  # type: ignore[arg-type]

    assert outcomes[0].ok is True
    assert outcomes[0].content is not None
    assert b"script" not in outcomes[0].content


def test_fetch_media_rejects_svg_when_disallowed() -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
    downloader = _FakeDownloader(
        results_by_url={
            "https://example.org/a.svg": MediaDownloadResult(
                content=svg, content_type="image/svg+xml"
            )
        }
    )
    plan = (MediaPlanEntry(page_id=1, media=_media("https://example.org/a.svg")),)

    outcomes = fetch_media(plan, downloader=downloader, max_pixels=10_000, allow_svg=False)  # type: ignore[arg-type]

    assert outcomes[0].ok is False


def test_fetch_media_rejects_content_over_pixel_limit() -> None:
    downloader = _FakeDownloader(
        results_by_url={
            "https://example.org/a.png": MediaDownloadResult(
                content=_png_bytes(), content_type="image/png"
            ),
        }
    )
    plan = (MediaPlanEntry(page_id=1, media=_media("https://example.org/a.png")),)

    outcomes = fetch_media(plan, downloader=downloader, max_pixels=1, allow_svg=True)  # type: ignore[arg-type]

    assert outcomes[0].ok is False


def test_fetch_media_with_multiple_workers_preserves_plan_order() -> None:
    urls = [f"https://example.org/{index}.png" for index in range(8)]
    downloader = _FakeDownloader(
        results_by_url={
            url: MediaDownloadResult(content=_png_bytes(), content_type="image/png") for url in urls
        }
    )
    plan = tuple(MediaPlanEntry(page_id=index, media=_media(url)) for index, url in enumerate(urls))

    outcomes = fetch_media(
        plan, downloader=downloader, max_pixels=10_000, allow_svg=True, max_workers=4
    )  # type: ignore[arg-type]

    assert [outcome.source_url for outcome in outcomes] == urls
    assert all(outcome.ok for outcome in outcomes)


def test_fetch_media_rejects_non_positive_max_workers() -> None:
    downloader = _FakeDownloader()
    plan = (MediaPlanEntry(page_id=1, media=_media("https://example.org/a.png")),)

    with pytest.raises(ValueError, match="max_workers"):
        fetch_media(plan, downloader=downloader, max_pixels=10_000, allow_svg=True, max_workers=0)  # type: ignore[arg-type]


def test_fetch_media_limit_stops_after_n_unique_urls() -> None:
    urls = [f"https://example.org/{index}.png" for index in range(5)]
    downloader = _FakeDownloader(
        results_by_url={
            url: MediaDownloadResult(content=_png_bytes(), content_type="image/png") for url in urls
        }
    )
    plan = tuple(MediaPlanEntry(page_id=index, media=_media(url)) for index, url in enumerate(urls))

    outcomes = fetch_media(plan, downloader=downloader, max_pixels=10_000, allow_svg=True, limit=2)  # type: ignore[arg-type]

    assert [outcome.source_url for outcome in outcomes] == urls[:2]


def test_fetch_media_limit_counts_unique_urls_not_plan_entries() -> None:
    downloader = _FakeDownloader(
        results_by_url={
            "https://example.org/a.png": MediaDownloadResult(
                content=_png_bytes(), content_type="image/png"
            ),
        }
    )
    plan = (
        MediaPlanEntry(page_id=1, media=_media("https://example.org/a.png")),
        MediaPlanEntry(page_id=2, media=_media("https://example.org/a.png")),
    )

    outcomes = fetch_media(plan, downloader=downloader, max_pixels=10_000, allow_svg=True, limit=1)  # type: ignore[arg-type]

    assert len(outcomes) == 1


def test_fetch_media_rejects_negative_limit() -> None:
    downloader = _FakeDownloader()
    plan = (MediaPlanEntry(page_id=1, media=_media("https://example.org/a.png")),)

    with pytest.raises(ValueError, match="limit"):
        fetch_media(plan, downloader=downloader, max_pixels=10_000, allow_svg=True, limit=-1)  # type: ignore[arg-type]


def test_fetch_media_reports_progress_sequentially() -> None:
    urls = [f"https://example.org/{index}.png" for index in range(3)]
    downloader = _FakeDownloader(
        results_by_url={
            url: MediaDownloadResult(content=_png_bytes(), content_type="image/png") for url in urls
        }
    )
    plan = tuple(MediaPlanEntry(page_id=index, media=_media(url)) for index, url in enumerate(urls))
    events: list[FetchProgress] = []

    fetch_media(
        plan,
        downloader=downloader,  # type: ignore[arg-type]
        max_pixels=10_000,
        allow_svg=True,
        on_progress=events.append,
    )

    assert [event.completed for event in events] == [1, 2, 3]
    assert [event.total for event in events] == [3, 3, 3]
    assert events[-1].succeeded == 3
    assert events[-1].failed == 0


def test_fetch_media_reports_progress_with_multiple_workers() -> None:
    urls = [f"https://example.org/{index}.png" for index in range(6)]
    downloader = _FakeDownloader(
        results_by_url={
            url: MediaDownloadResult(content=_png_bytes(), content_type="image/png") for url in urls
        }
    )
    plan = tuple(MediaPlanEntry(page_id=index, media=_media(url)) for index, url in enumerate(urls))
    events: list[FetchProgress] = []

    fetch_media(
        plan,
        downloader=downloader,  # type: ignore[arg-type]
        max_pixels=10_000,
        allow_svg=True,
        max_workers=3,
        on_progress=events.append,
    )

    assert [event.completed for event in events] == list(range(1, 7))
    assert events[-1].succeeded == 6
    assert events[-1].failed == 0


def test_fetch_media_progress_counts_failures() -> None:
    downloader = _FakeDownloader(
        results_by_url={"https://example.org/a.png": MediaDownloadError("boom")}
    )
    plan = (MediaPlanEntry(page_id=1, media=_media("https://example.org/a.png")),)
    events: list[FetchProgress] = []

    fetch_media(
        plan,
        downloader=downloader,  # type: ignore[arg-type]
        max_pixels=10_000,
        allow_svg=True,
        on_progress=events.append,
    )

    assert events[-1].succeeded == 0
    assert events[-1].failed == 1


@_requires_imagemagick
def test_convert_media_converts_successful_fetches(tmp_path: Path) -> None:
    cache = MediaCache(tmp_path)
    outcomes = (_fetch_outcome("https://example.org/a.png", _png_bytes(), content_hash="hash1"),)

    progress = []
    result = convert_media(outcomes, cache=cache, on_progress=progress.append)

    assert len(result) == 1
    assert result[0].source_url == "https://example.org/a.png"
    assert result[0].bmp_bytes.startswith(b"BM")
    assert progress[-1].phase == "image-convert"
    assert progress[-1].complete is True


@_requires_imagemagick
def test_convert_media_skips_failed_fetches(tmp_path: Path) -> None:
    cache = MediaCache(tmp_path)
    outcomes = (
        FetchOutcome(
            source_url="https://example.org/bad.png",
            content=None,
            content_hash=None,
            detected_format=None,
            error="download failed",
        ),
    )

    result = convert_media(outcomes, cache=cache)

    assert result == ()


@_requires_imagemagick
def test_convert_media_deduplicates_identical_content(tmp_path: Path) -> None:
    cache = MediaCache(tmp_path)
    content = _png_bytes()
    outcomes = (
        _fetch_outcome("https://example.org/a.png", content, content_hash="same-hash"),
        _fetch_outcome("https://example.org/b.png", content, content_hash="same-hash"),
    )

    result = convert_media(outcomes, cache=cache)

    assert len(result) == 1
    assert result[0].source_url == "https://example.org/a.png"


def test_convert_media_with_no_outcomes_returns_empty(tmp_path: Path) -> None:
    cache = MediaCache(tmp_path)

    assert convert_media((), cache=cache) == ()


def test_write_and_read_fetch_report_round_trips(tmp_path: Path) -> None:
    from wikiepwing.media.orchestrate import read_fetch_report, write_fetch_report

    outcomes = (
        _fetch_outcome("https://example.org/a.png", b"content-a", content_hash="hash-a"),
        FetchOutcome(
            source_url="https://example.org/bad.png",
            content=None,
            content_hash=None,
            detected_format=None,
            error="download failed",
        ),
    )
    originals_dir = tmp_path / "originals"
    report_path = tmp_path / "fetch-report.json"

    write_fetch_report(outcomes, originals_dir=originals_dir, report_path=report_path)
    restored = read_fetch_report(report_path, originals_dir=originals_dir)

    assert restored == outcomes


def test_write_fetch_report_stores_bytes_by_content_hash(tmp_path: Path) -> None:
    from wikiepwing.media.orchestrate import write_fetch_report

    outcomes = (_fetch_outcome("https://example.org/a.png", b"content-a", content_hash="hash-a"),)
    originals_dir = tmp_path / "originals"

    write_fetch_report(outcomes, originals_dir=originals_dir, report_path=tmp_path / "report.json")

    assert (originals_dir / "hash-a.bin").read_bytes() == b"content-a"
