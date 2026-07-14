from __future__ import annotations

from datetime import UTC, datetime

import pytest

from wikiepwing.config import AppConfig, PathsConfig
from wikiepwing.model.article import Article
from wikiepwing.model.blocks import Block, ParagraphBlock, QuoteBlock
from wikiepwing.model.diagnostics import Diagnostic
from wikiepwing.model.inline import InternalLinkInline, TextInline
from wikiepwing.model.validate import (
    ModelValidationConfigError,
    ModelValidationLimits,
    validate_article,
)


def _make_article(**overrides: object) -> Article:
    defaults: dict[str, object] = {
        "page_id": 123,
        "revision_id": 456,
        "title": "Emacs",
        "normalized_title": "Emacs",
        "source_url": "https://ja.wikipedia.org/wiki/Emacs",
        "source_date_modified": datetime(2026, 1, 1, tzinfo=UTC),
        "abstract": None,
        "blocks": (),
        "aliases": (),
        "categories": (),
        "media": (),
        "diagnostics": (),
        "source_license_ids": ("CC-BY-SA-3.0",),
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def _make_app_config(model_section: dict[str, object]) -> AppConfig:
    paths = PathsConfig(
        sources=None,  # type: ignore[arg-type]
        reference=None,  # type: ignore[arg-type]
        work=None,  # type: ignore[arg-type]
        cache=None,  # type: ignore[arg-type]
        output=None,  # type: ignore[arg-type]
        reports=None,  # type: ignore[arg-type]
        logs=None,  # type: ignore[arg-type]
    )
    return AppConfig(
        schema_version=1,
        project="wikiepwing",
        profile="test",
        paths=paths,
        source_files=(),
        _values={"model": model_section},
    )


def test_validate_article_accepts_empty_article() -> None:
    article = _make_article()
    limits = ModelValidationLimits(max_block_nesting_depth=32)

    diagnostics = validate_article(article, limits)

    assert diagnostics == ()


def test_validate_article_accepts_shallow_nesting() -> None:
    article = _make_article(
        blocks=(QuoteBlock(blocks=(ParagraphBlock(inlines=(TextInline("hi"),)),)),)
    )
    limits = ModelValidationLimits(max_block_nesting_depth=32)

    diagnostics = validate_article(article, limits)

    assert diagnostics == ()


def test_validate_article_rejects_nesting_beyond_limit() -> None:
    inner: Block = ParagraphBlock(inlines=(TextInline("deep"),))
    for _ in range(5):
        inner = QuoteBlock(blocks=(inner,))
    article = _make_article(blocks=(inner,))
    limits = ModelValidationLimits(max_block_nesting_depth=2)

    diagnostics = validate_article(article, limits)

    codes = {d.code for d in diagnostics}
    assert "MODEL_BLOCK_NESTING_TOO_DEEP" in codes


def test_validate_article_rejects_resolved_link_without_page_id() -> None:
    article = _make_article(
        blocks=(
            ParagraphBlock(
                inlines=(
                    InternalLinkInline(
                        label=(TextInline("GNU Emacs"),),
                        target_title="GNU Emacs",
                        target_normalized_title="GNU Emacs",
                        target_fragment=None,
                        target_page_id=None,
                        resolution="resolved",
                    ),
                ),
            ),
        )
    )
    limits = ModelValidationLimits(max_block_nesting_depth=32)

    diagnostics = validate_article(article, limits)

    codes = {d.code for d in diagnostics}
    assert "MODEL_LINK_RESOLVED_WITHOUT_PAGE_ID" in codes


def test_validate_article_rejects_missing_link_with_page_id() -> None:
    article = _make_article(
        blocks=(
            ParagraphBlock(
                inlines=(
                    InternalLinkInline(
                        label=(TextInline("Ghost"),),
                        target_title="Ghost",
                        target_normalized_title="Ghost",
                        target_fragment=None,
                        target_page_id=999,
                        resolution="missing",
                    ),
                ),
            ),
        )
    )
    limits = ModelValidationLimits(max_block_nesting_depth=32)

    diagnostics = validate_article(article, limits)

    codes = {d.code for d in diagnostics}
    assert "MODEL_LINK_UNRESOLVED_WITH_PAGE_ID" in codes


def test_validate_article_accepts_consistent_resolved_link() -> None:
    article = _make_article(
        blocks=(
            ParagraphBlock(
                inlines=(
                    InternalLinkInline(
                        label=(TextInline("GNU Emacs"),),
                        target_title="GNU Emacs",
                        target_normalized_title="GNU Emacs",
                        target_fragment=None,
                        target_page_id=42,
                        resolution="resolved",
                    ),
                ),
            ),
        )
    )
    limits = ModelValidationLimits(max_block_nesting_depth=32)

    diagnostics = validate_article(article, limits)

    assert diagnostics == ()


def test_validate_article_rejects_diagnostic_page_id_mismatch() -> None:
    article = _make_article(
        diagnostics=(
            Diagnostic(
                code="REC_TEST",
                severity="info",
                stage="ingest",
                page_id=999,
                title=None,
                message="test",
                source_path=None,
                source_excerpt=None,
                details={},
            ),
        )
    )
    limits = ModelValidationLimits(max_block_nesting_depth=32)

    diagnostics = validate_article(article, limits)

    codes = {d.code for d in diagnostics}
    assert "MODEL_DIAGNOSTIC_PAGE_ID_MISMATCH" in codes


def test_validate_article_rejects_diagnostic_title_mismatch() -> None:
    article = _make_article(
        diagnostics=(
            Diagnostic(
                code="REC_TEST",
                severity="info",
                stage="ingest",
                page_id=None,
                title="Other Title",
                message="test",
                source_path=None,
                source_excerpt=None,
                details={},
            ),
        )
    )
    limits = ModelValidationLimits(max_block_nesting_depth=32)

    diagnostics = validate_article(article, limits)

    codes = {d.code for d in diagnostics}
    assert "MODEL_DIAGNOSTIC_TITLE_MISMATCH" in codes


def test_validate_article_accepts_consistent_diagnostic() -> None:
    article = _make_article(
        diagnostics=(
            Diagnostic(
                code="REC_TEST",
                severity="info",
                stage="ingest",
                page_id=123,
                title="Emacs",
                message="test",
                source_path=None,
                source_excerpt=None,
                details={},
            ),
        )
    )
    limits = ModelValidationLimits(max_block_nesting_depth=32)

    diagnostics = validate_article(article, limits)

    assert diagnostics == ()


def test_model_validation_limits_rejects_non_positive_depth() -> None:
    with pytest.raises(ModelValidationConfigError, match="max_block_nesting_depth"):
        ModelValidationLimits(max_block_nesting_depth=0)


def test_model_validation_limits_from_config() -> None:
    config = _make_app_config({"max_block_nesting_depth": 16})

    limits = ModelValidationLimits.from_config(config)

    assert limits.max_block_nesting_depth == 16
