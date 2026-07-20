from __future__ import annotations

import pytest

from wikiepwing.links.external_policy import (
    ExternalLinkPolicyError,
    apply_external_link_policy,
)
from wikiepwing.model.inline import ExternalLinkInline, TextInline

_LABEL = (TextInline(value="GNU"),)


def test_https_url_becomes_external_link_inline() -> None:
    result = apply_external_link_policy(_LABEL, "https://gnu.org", "plain-text")

    assert result == (ExternalLinkInline(label=_LABEL, url="https://gnu.org"),)


def test_http_url_becomes_external_link_inline() -> None:
    result = apply_external_link_policy(_LABEL, "http://gnu.org", "plain-text")

    assert result == (ExternalLinkInline(label=_LABEL, url="http://gnu.org"),)


def test_protocol_relative_url_is_treated_as_https() -> None:
    result = apply_external_link_policy(_LABEL, "//gnu.org/path", "plain-text")

    assert result == (ExternalLinkInline(label=_LABEL, url="https://gnu.org/path"),)


def test_javascript_scheme_falls_back_to_label_only() -> None:
    result = apply_external_link_policy(_LABEL, "javascript:alert(1)", "plain-text")

    assert result == _LABEL


def test_data_scheme_falls_back_to_label_only() -> None:
    result = apply_external_link_policy(_LABEL, "data:text/html,<script>x</script>", "plain-text")

    assert result == _LABEL


def test_scheme_without_netloc_falls_back_to_label_only() -> None:
    result = apply_external_link_policy(_LABEL, "mailto:someone", "plain-text")

    assert result == _LABEL


def test_nfkc_invalid_netloc_falls_back_to_label_only() -> None:
    result = apply_external_link_policy(_LABEL, "https://www.thefirstt？imes.jp", "plain-text")

    assert result == _LABEL


def test_unknown_policy_is_rejected() -> None:
    with pytest.raises(ExternalLinkPolicyError, match="policy"):
        apply_external_link_policy(_LABEL, "https://gnu.org", "footnote")


def test_empty_label_is_preserved_on_fallback() -> None:
    result = apply_external_link_policy((), "javascript:alert(1)", "plain-text")

    assert result == ()
