from __future__ import annotations

import pytest

from wikiepwing.model.inline import (
    CodeInline,
    EmphasisInline,
    ExternalLinkInline,
    InlineError,
    InternalLinkInline,
    LineBreakInline,
    StrongInline,
    TextInline,
    UnsupportedInline,
    inline_payload,
    parse_inline,
)


def test_text_inline_round_trips() -> None:
    inline = TextInline(value="Emacs")

    restored = parse_inline(inline_payload(inline))

    assert restored == inline
    assert inline.payload() == {"type": "text", "value": "Emacs"}


def test_strong_inline_round_trips_with_nested_text() -> None:
    inline = StrongInline(inlines=(TextInline("bold"),))

    restored = parse_inline(inline_payload(inline))

    assert restored == inline


def test_emphasis_inline_round_trips() -> None:
    inline = EmphasisInline(inlines=(TextInline("italic"),))

    restored = parse_inline(inline_payload(inline))

    assert restored == inline


def test_code_inline_round_trips() -> None:
    inline = CodeInline(value="int main()")

    restored = parse_inline(inline_payload(inline))

    assert restored == inline


def test_line_break_inline_round_trips() -> None:
    inline = LineBreakInline()

    restored = parse_inline(inline_payload(inline))

    assert restored == inline
    assert inline.payload() == {"type": "line_break"}


def test_internal_link_inline_round_trips() -> None:
    inline = InternalLinkInline(
        label=(TextInline("GNU Emacs"),),
        target_title="GNU Emacs",
        target_normalized_title="GNU Emacs",
        target_fragment=None,
        target_page_id=1234,
        resolution="resolved",
    )

    restored = parse_inline(inline_payload(inline))

    assert restored == inline


def test_internal_link_inline_round_trips_with_missing_resolution() -> None:
    inline = InternalLinkInline(
        label=(TextInline("Ghost Page"),),
        target_title="Ghost Page",
        target_normalized_title="Ghost Page",
        target_fragment="History",
        target_page_id=None,
        resolution="missing",
    )

    restored = parse_inline(inline_payload(inline))

    assert restored == inline


def test_internal_link_inline_rejects_invalid_resolution() -> None:
    with pytest.raises(InlineError, match="resolution"):
        InternalLinkInline(
            label=(),
            target_title="x",
            target_normalized_title="x",
            target_fragment=None,
            target_page_id=None,
            resolution="ignored",  # type: ignore[arg-type]
        )


def test_internal_link_inline_rejects_empty_target_title() -> None:
    with pytest.raises(InlineError, match="target_title"):
        InternalLinkInline(
            label=(),
            target_title="",
            target_normalized_title="x",
            target_fragment=None,
            target_page_id=None,
            resolution="resolved",
        )


def test_external_link_inline_round_trips() -> None:
    inline = ExternalLinkInline(label=(TextInline("GNU"),), url="https://gnu.org")

    restored = parse_inline(inline_payload(inline))

    assert restored == inline


def test_external_link_inline_rejects_empty_url() -> None:
    with pytest.raises(InlineError, match="url"):
        ExternalLinkInline(label=(), url="")


def test_unsupported_inline_round_trips() -> None:
    inline = UnsupportedInline(
        element_name="custom-tag",
        fallback_text="visible text",
        diagnostic_code="DOM_UNKNOWN_ELEMENT",
    )

    restored = parse_inline(inline_payload(inline))

    assert restored == inline


def test_unsupported_inline_rejects_empty_element_name() -> None:
    with pytest.raises(InlineError, match="element_name"):
        UnsupportedInline(element_name="", fallback_text="", diagnostic_code="X")


def test_parse_inline_rejects_non_object() -> None:
    with pytest.raises(InlineError, match="JSON object"):
        parse_inline(["not", "an", "object"])


def test_parse_inline_rejects_unknown_type() -> None:
    with pytest.raises(InlineError, match="unknown inline type"):
        parse_inline({"type": "ruby"})


def test_parse_inline_rejects_missing_type() -> None:
    with pytest.raises(InlineError, match="unknown inline type"):
        parse_inline({"value": "x"})


def test_nested_strong_inside_emphasis_round_trips() -> None:
    inline = EmphasisInline(inlines=(StrongInline(inlines=(TextInline("both"),)),))

    restored = parse_inline(inline_payload(inline))

    assert restored == inline


def test_internal_link_missing_label_field_is_rejected() -> None:
    payload = {
        "type": "internal_link",
        "target_title": "x",
        "target_normalized_title": "x",
        "target_fragment": None,
        "target_page_id": None,
        "resolution": "resolved",
    }

    with pytest.raises(InlineError, match="label"):
        parse_inline(payload)
