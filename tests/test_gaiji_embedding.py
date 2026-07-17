from __future__ import annotations

from wikiepwing.gaiji.embedding import (
    GaijiPlan,
    embed_gaiji_tokens,
    embed_title_fallback,
    gaiji_width_class,
    plan_gaiji_codes,
)
from wikiepwing.gaiji.unrepresentable import UnrepresentableTracker

# U+4E02, JIS X 0212-only (SS3) kanji: real EUC-JP body text hits this.
_SS3_KANJI = "丂"
# East Asian Wide by Unicode's east_asian_width property.
_WIDE_KANJI = "蔦"


def test_gaiji_width_class_classifies_wide_kanji_as_wide() -> None:
    assert gaiji_width_class(_WIDE_KANJI) == "wide"


def test_gaiji_width_class_classifies_ascii_as_narrow() -> None:
    assert gaiji_width_class("A") == "narrow"


def test_plan_gaiji_codes_is_empty_for_fully_representable_text() -> None:
    plan = plan_gaiji_codes(["東京タワー", "Emacs"])

    assert plan.is_empty()


def test_plan_gaiji_codes_assigns_deterministic_codes_to_candidates() -> None:
    plan = plan_gaiji_codes([f"before {_SS3_KANJI} after"])

    assert not plan.is_empty()
    assert plan.assigned_codes[_SS3_KANJI] == "wide-0001"
    assert plan.width_classes[_SS3_KANJI] == "wide"
    assert plan.usage_counts[_SS3_KANJI] == 1


def test_plan_gaiji_codes_counts_every_occurrence() -> None:
    plan = plan_gaiji_codes([_SS3_KANJI, f"{_SS3_KANJI}{_SS3_KANJI}"])

    assert plan.usage_counts[_SS3_KANJI] == 3


def test_plan_gaiji_codes_is_processing_order_independent() -> None:
    first = plan_gaiji_codes(["b" + _SS3_KANJI, "a" + _WIDE_KANJI])
    second = plan_gaiji_codes(["a" + _WIDE_KANJI, "b" + _SS3_KANJI])

    assert first.assigned_codes == second.assigned_codes


def test_embed_gaiji_tokens_keeps_representable_text_unchanged() -> None:
    plan = GaijiPlan(assigned_codes={}, width_classes={}, usage_counts={})

    assert embed_gaiji_tokens("東京タワー", plan=plan) == "東京タワー"


def test_embed_gaiji_tokens_replaces_gaiji_candidate_with_token() -> None:
    plan = plan_gaiji_codes([f"a{_SS3_KANJI}b"])

    result = embed_gaiji_tokens(f"a{_SS3_KANJI}b", plan=plan)

    assert result == "a@@GAIJI:wide-0001@@b"


def test_embed_gaiji_tokens_falls_back_to_bracket_notation_for_category_d() -> None:
    plan = GaijiPlan(assigned_codes={}, width_classes={}, usage_counts={})

    result = embed_gaiji_tokens("a\U0001f600b", plan=plan)

    assert result == "a[U+1F600]b"


def test_embed_gaiji_tokens_records_category_d_occurrences_in_tracker() -> None:
    plan = GaijiPlan(assigned_codes={}, width_classes={}, usage_counts={})
    tracker = UnrepresentableTracker()

    embed_gaiji_tokens("\U0001f600", plan=plan, tracker=tracker, page_id=7, title="Some Article")

    stats = tracker.most_frequent()
    assert len(stats) == 1
    assert stats[0].character == "\U0001f600"
    assert stats[0].examples[0].page_id == 7
    assert stats[0].examples[0].title == "Some Article"


def test_embed_gaiji_tokens_applies_safe_substitutions_first() -> None:
    plan = GaijiPlan(assigned_codes={}, width_classes={}, usage_counts={})

    # Non-breaking space -> normal space (18.2), not a gaiji/D fallback.
    assert embed_gaiji_tokens("a b", plan=plan) == "a b"


def test_embed_title_fallback_keeps_representable_text_unchanged() -> None:
    assert embed_title_fallback("Emacs") == "Emacs"


def test_embed_title_fallback_never_produces_a_gaiji_token() -> None:
    result = embed_title_fallback(f"Title {_SS3_KANJI}")

    assert "@@GAIJI:" not in result
    assert result == "Title [U+4E02]"


def test_embed_title_fallback_records_occurrences_in_tracker() -> None:
    tracker = UnrepresentableTracker()

    embed_title_fallback(_SS3_KANJI, tracker=tracker, page_id=3, title="T")

    assert tracker.total_occurrences() == 1
