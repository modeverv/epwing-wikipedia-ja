from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wikiepwing.ingest.database import connect_raw_database, initialize_raw_database
from wikiepwing.ingest.deduplicate import DuplicateRecord
from wikiepwing.ingest.record_parser import LicenseRecord, RawArticle, SourceImage, parse_record
from wikiepwing.ingest.repository import RawRepository, RawRepositoryError, normalize_title
from wikiepwing.ingest.validate import Diagnostic
from wikiepwing.ingest.zstd_codec import decompress

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "raw"
NORMAL_PATH = Path("tests/fixtures/enterprise/normal_articles.ndjson")


def _connection(tmp_path: Path) -> sqlite3.Connection:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    return connect_raw_database(database)


def _article(**overrides: object) -> RawArticle:
    defaults: dict[str, object] = {
        "page_id": 1,
        "revision_id": 1,
        "title": "Emacs",
        "namespace_id": 0,
        "url": "https://ja.wikipedia.org/wiki/Emacs",
        "date_modified": datetime(2026, 6, 1, tzinfo=UTC),
        "html": "<p>hello</p>",
        "wikitext": "hello",
        "redirects": ("GNU Emacs",),
        "categories": ("Category:Emacs",),
        "templates": ("Template:Infobox",),
        "licenses": (LicenseRecord("CC-BY-SA-4.0", "CC BY-SA 4.0", "https://example/license"),),
        "main_image": SourceImage("https://example/image.png", 100, 200),
        "source_sequence": 0,
        "source_hash": "a" * 64,
    }
    defaults.update(overrides)
    return RawArticle(**defaults)  # type: ignore[arg-type]


def test_rejects_connection_without_foreign_keys(tmp_path: Path) -> None:
    database = initialize_raw_database(tmp_path / "raw.sqlite3", MIGRATIONS)
    connection = sqlite3.connect(database)

    with pytest.raises(RawRepositoryError, match="foreign_keys"):
        RawRepository(connection)


def test_write_accepted_article_stores_compressed_body_and_children(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)
    article = _article()

    with repository.batch():
        repository.write_accepted_article(article)

    row = connection.execute(
        "SELECT title, normalized_title, html_zstd, wikitext_zstd, ingest_status, source_hash "
        "FROM articles WHERE page_id = ?",
        (article.page_id,),
    ).fetchone()
    assert row["title"] == "Emacs"
    assert row["normalized_title"] == normalize_title("Emacs")
    assert decompress(row["html_zstd"]) == article.html.encode("utf-8")
    assert decompress(row["wikitext_zstd"]) == article.wikitext.encode("utf-8")
    assert row["ingest_status"] == "accepted"
    assert row["source_hash"] == article.source_hash

    redirects = connection.execute(
        "SELECT redirect_title FROM redirects WHERE target_page_id = ?", (article.page_id,)
    ).fetchall()
    assert [r["redirect_title"] for r in redirects] == ["GNU Emacs"]

    categories = connection.execute(
        "SELECT category_name FROM categories WHERE page_id = ?", (article.page_id,)
    ).fetchall()
    assert [c["category_name"] for c in categories] == ["Category:Emacs"]

    templates = connection.execute(
        "SELECT template_name FROM templates WHERE page_id = ?", (article.page_id,)
    ).fetchall()
    assert [t["template_name"] for t in templates] == ["Template:Infobox"]

    licenses = connection.execute(
        """
        SELECT l.identifier FROM article_licenses al
        JOIN licenses l ON l.license_id = al.license_id
        WHERE al.page_id = ?
        """,
        (article.page_id,),
    ).fetchall()
    assert [row["identifier"] for row in licenses] == ["CC-BY-SA-4.0"]

    image = connection.execute(
        "SELECT content_url, width, height FROM main_images WHERE page_id = ?", (article.page_id,)
    ).fetchone()
    assert image["content_url"] == "https://example/image.png"
    assert image["width"] == 100
    assert image["height"] == 200

    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_write_accepted_article_with_no_html_or_wikitext(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)
    article = _article(html=None, wikitext=None)

    with repository.batch():
        repository.write_accepted_article(article)

    row = connection.execute(
        "SELECT html_zstd, wikitext_zstd FROM articles WHERE page_id = ?", (article.page_id,)
    ).fetchone()
    assert row["html_zstd"] is None
    assert row["wikitext_zstd"] is None


def test_replacing_article_clears_old_children(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)
    first = _article(revision_id=1, redirects=("Old Redirect",), source_hash="a" * 64)

    with repository.batch():
        repository.write_accepted_article(first)

    second = _article(revision_id=2, redirects=("New Redirect",), source_hash="b" * 64)
    with repository.batch():
        repository.write_accepted_article(second)

    redirects = connection.execute(
        "SELECT redirect_title FROM redirects WHERE target_page_id = ?", (first.page_id,)
    ).fetchall()
    assert [r["redirect_title"] for r in redirects] == ["New Redirect"]

    row = connection.execute(
        "SELECT revision_id, source_hash FROM articles WHERE page_id = ?", (first.page_id,)
    ).fetchone()
    assert row["revision_id"] == 2
    assert row["source_hash"] == "b" * 64


def test_write_rejected_article_has_no_children_or_body(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)
    article = _article()

    with repository.batch():
        repository.write_rejected_article(article)

    row = connection.execute(
        "SELECT ingest_status, html_zstd, wikitext_zstd FROM articles WHERE page_id = ?",
        (article.page_id,),
    ).fetchone()
    assert row["ingest_status"] == "rejected"
    assert row["html_zstd"] is None
    assert row["wikitext_zstd"] is None

    redirects = connection.execute(
        "SELECT * FROM redirects WHERE target_page_id = ?", (article.page_id,)
    ).fetchall()
    assert redirects == []


def test_get_existing_accepted_ignores_rejected_rows(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)
    article = _article()

    with repository.batch():
        repository.write_rejected_article(article)

    assert repository.get_existing_accepted(article.page_id) is None


def test_get_existing_accepted_returns_state_for_accepted_row(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)
    article = _article()

    with repository.batch():
        repository.write_accepted_article(article)

    existing = repository.get_existing_accepted(article.page_id)
    assert existing is not None
    assert existing.revision_id == article.revision_id
    assert existing.source_hash == article.source_hash
    assert existing.source_sequence == article.source_sequence


def test_write_duplicate_inserts_row(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)
    article = _article()
    with repository.batch():
        repository.write_accepted_article(article)

    record = DuplicateRecord(
        page_id=article.page_id,
        kept_revision_id=2,
        dropped_revision_id=1,
        kept_hash="b" * 64,
        dropped_hash="a" * 64,
        reason="newer_revision_replaced_older",
        source_sequence=5,
    )
    with repository.batch():
        repository.write_duplicate(record)

    row = connection.execute(
        "SELECT page_id, kept_revision_id, dropped_revision_id, reason, source_sequence "
        "FROM ingest_duplicates"
    ).fetchone()
    assert row["page_id"] == article.page_id
    assert row["kept_revision_id"] == 2
    assert row["reason"] == "newer_revision_replaced_older"


def test_write_diagnostic_inserts_row(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)
    diagnostic = Diagnostic(
        code="REC_REVISION_HASH_CONFLICT",
        severity="error",
        message="conflict",
        details={"page_id": 1},
    )

    with repository.batch():
        repository.write_diagnostic(diagnostic, stage="ingest", page_id=1, title="Emacs")

    row = connection.execute(
        "SELECT code, severity, stage, page_id, title, message, details_json FROM diagnostics"
    ).fetchone()
    assert row["code"] == "REC_REVISION_HASH_CONFLICT"
    assert row["severity"] == "error"
    assert row["stage"] == "ingest"
    assert row["page_id"] == 1
    assert row["title"] == "Emacs"
    assert json.loads(row["details_json"]) == {"page_id": 1}


def test_batch_rolls_back_on_exception(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)

    with pytest.raises(RuntimeError, match="boom"):
        with repository.batch():
            repository.write_accepted_article(_article())
            raise RuntimeError("boom")

    count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert count == 0


def test_batch_commits_multiple_writes_together(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)

    with repository.batch():
        for i in range(5):
            repository.write_accepted_article(_article(page_id=i, source_hash=f"{i}" * 64))

    count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert count == 5


def test_writes_all_ten_normal_fixture_articles(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    repository = RawRepository(connection)
    lines = [
        line.encode("utf-8")
        for line in NORMAL_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    articles = [parse_record(line, source_sequence=i) for i, line in enumerate(lines)]

    with repository.batch():
        for article in articles:
            repository.write_accepted_article(article)

    count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert count == 10
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
