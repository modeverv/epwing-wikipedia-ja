from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from wikiepwing.model.article import Article, MediaReference
from wikiepwing.model.blocks import ListItem, ParagraphBlock, ReferencesBlock, UnorderedListBlock
from wikiepwing.model.canonical import encode_article
from wikiepwing.model.database import connect_model_database, initialize_model_database
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import InternalLinkInline, TextInline
from wikiepwing.model.logical_hash import compute_logical_hash
from wikiepwing.model.repository import ModelRepository

MIGRATIONS = Path(__file__).parents[1] / "migrations" / "model"


def _make_article(**overrides: object) -> Article:
    defaults: dict[str, object] = {
        "page_id": 1,
        "revision_id": 100,
        "title": "Emacs",
        "normalized_title": "Emacs",
        "source_url": "https://ja.wikipedia.org/wiki/Emacs",
        "source_date_modified": datetime(2026, 1, 1, tzinfo=UTC),
        "abstract": "An extensible editor.",
        "blocks": (
            ParagraphBlock(
                inlines=(
                    TextInline(value="See "),
                    InternalLinkInline(
                        label=(TextInline(value="GNU Emacs"),),
                        target_title="GNU Emacs",
                        target_normalized_title="GNU Emacs",
                        target_fragment=None,
                        target_page_id=42,
                        resolution="resolved",
                    ),
                )
            ),
        ),
        "aliases": (),
        "categories": (),
        "media": (
            MediaReference(
                media_id="File:Emacs.png",
                source_url="https://upload.wikimedia.org/Emacs.png",
                source_name="Emacs.png",
                alt_text="screenshot",
                caption=None,
                role="main",
                source_width=640,
                source_height=480,
            ),
        ),
        "diagnostics": (
            Diagnostic(
                code="MODEL_TEST",
                severity="info",
                stage="normalize_test",
                page_id=1,
                title="Emacs",
                message="test diagnostic",
                source_path=None,
                source_excerpt=None,
                details={},
            ),
        ),
        "source_license_ids": ("CC-BY-SA-3.0",),
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def test_write_article_inserts_row_and_children(tmp_path: Path) -> None:
    database = initialize_model_database(tmp_path / "model.sqlite3", MIGRATIONS)
    article = _make_article()

    with connect_model_database(database) as connection:
        repository = ModelRepository(connection)
        canonical_json = encode_article(article)
        logical_hash = compute_logical_hash(article)
        with repository.batch():
            repository.write_article(
                article,
                canonical_json=canonical_json,
                logical_hash=logical_hash,
                normalize_status="complete",
            )

        row = connection.execute(
            "SELECT title, normalize_status, block_count, diagnostic_count, article_logical_hash "
            "FROM articles WHERE page_id = ?",
            (1,),
        ).fetchone()
        assert row["title"] == "Emacs"
        assert row["normalize_status"] == "complete"
        assert row["block_count"] == 1
        assert row["diagnostic_count"] == 1
        assert row["article_logical_hash"] == logical_hash

        link_row = connection.execute(
            "SELECT target_page_id, target_title, resolution FROM links WHERE source_page_id = ?",
            (1,),
        ).fetchone()
        assert link_row["target_page_id"] == 42
        assert link_row["target_title"] == "GNU Emacs"
        assert link_row["resolution"] == "resolved"

        media_row = connection.execute(
            "SELECT media_id, role FROM media_references WHERE page_id = ?", (1,)
        ).fetchone()
        assert media_row["media_id"] == "File:Emacs.png"
        assert media_row["role"] == "main"

        diagnostic_row = connection.execute(
            "SELECT code, message FROM diagnostics WHERE page_id = ?", (1,)
        ).fetchone()
        assert diagnostic_row["code"] == "MODEL_TEST"


def test_write_article_handles_references_block_alongside_lists(tmp_path: Path) -> None:
    # Regression test: ReferencesBlock.items (tuple[tuple[Inline, ...], ...]) and
    # UnorderedListBlock.items (tuple[ListItem, ...]) share a field name but different
    # shapes; the child-block walker must not confuse the two.
    database = initialize_model_database(tmp_path / "model.sqlite3", MIGRATIONS)
    article = _make_article(
        blocks=(
            UnorderedListBlock(
                items=(ListItem(blocks=(ParagraphBlock(inlines=(TextInline(value="item"),)),)),)
            ),
            ReferencesBlock(
                items=(
                    (
                        TextInline(value="A citation with a "),
                        InternalLinkInline(
                            label=(TextInline(value="link"),),
                            target_title="Some Page",
                            target_normalized_title="Some Page",
                            target_fragment=None,
                            target_page_id=7,
                            resolution="resolved",
                        ),
                    ),
                )
            ),
        )
    )

    with connect_model_database(database) as connection:
        repository = ModelRepository(connection)
        with repository.batch():
            repository.write_article(
                article,
                canonical_json=encode_article(article),
                logical_hash=compute_logical_hash(article),
                normalize_status="complete",
            )

        link_rows = connection.execute(
            "SELECT target_page_id FROM links WHERE source_page_id = ? ORDER BY ordinal", (1,)
        ).fetchall()
        assert {row["target_page_id"] for row in link_rows} == {7}


def test_write_article_replaces_children_on_rewrite(tmp_path: Path) -> None:
    database = initialize_model_database(tmp_path / "model.sqlite3", MIGRATIONS)
    article = _make_article()
    updated = _make_article(media=(), diagnostics=())

    with connect_model_database(database) as connection:
        repository = ModelRepository(connection)
        with repository.batch():
            repository.write_article(
                article,
                canonical_json=encode_article(article),
                logical_hash=compute_logical_hash(article),
                normalize_status="complete",
            )
        with repository.batch():
            repository.write_article(
                updated,
                canonical_json=encode_article(updated),
                logical_hash=compute_logical_hash(updated),
                normalize_status="complete",
            )

        media_count = connection.execute(
            "SELECT COUNT(*) FROM media_references WHERE page_id = ?", (1,)
        ).fetchone()[0]
        diagnostic_count = connection.execute(
            "SELECT COUNT(*) FROM diagnostics WHERE page_id = ?", (1,)
        ).fetchone()[0]
        assert media_count == 0
        assert diagnostic_count == 0
