from __future__ import annotations

import pytest

from wikiepwing.links.url_parser import ParsedInternalUrl, UrlParseError, parse_internal_url

_BASES = ("https://ja.wikipedia.org",)


def test_parses_site_relative_wiki_path() -> None:
    result = parse_internal_url("/wiki/Emacs", project_base_urls=_BASES)

    assert result == ParsedInternalUrl(namespace=None, title="Emacs", fragment=None)


def test_parses_full_url_matching_project_base() -> None:
    result = parse_internal_url("https://ja.wikipedia.org/wiki/Emacs", project_base_urls=_BASES)

    assert result == ParsedInternalUrl(namespace=None, title="Emacs", fragment=None)


def test_parses_document_relative_path() -> None:
    result = parse_internal_url("./Emacs", project_base_urls=_BASES)

    assert result == ParsedInternalUrl(namespace=None, title="Emacs", fragment=None)


def test_document_relative_redlink_query_is_not_part_of_title() -> None:
    result = parse_internal_url("./Missing_page?action=edit&redlink=1", project_base_urls=_BASES)

    assert result == ParsedInternalUrl(namespace=None, title="Missing page", fragment=None)


def test_separates_fragment() -> None:
    result = parse_internal_url("/wiki/Emacs#History", project_base_urls=_BASES)

    assert result == ParsedInternalUrl(namespace=None, title="Emacs", fragment="History")


def test_decodes_percent_encoding_and_underscores() -> None:
    result = parse_internal_url(
        "https://ja.wikipedia.org/wiki/GNU%E3%83%97%E3%83%AD%E3%82%B8%E3%82%A7%E3%82%AF%E3%83%88",
        project_base_urls=_BASES,
    )

    assert result is not None
    assert result.title == "GNUプロジェクト"


def test_underscore_becomes_space() -> None:
    result = parse_internal_url("/wiki/GNU_Emacs", project_base_urls=_BASES)

    assert result == ParsedInternalUrl(namespace=None, title="GNU Emacs", fragment=None)


def test_detects_known_namespace_prefix() -> None:
    result = parse_internal_url("/wiki/Category:Text_editors", project_base_urls=_BASES)

    assert result == ParsedInternalUrl(namespace="Category", title="Text editors", fragment=None)


def test_detects_japanese_namespace_prefix() -> None:
    result = parse_internal_url("./ファイル:Flag.svg", project_base_urls=_BASES)

    assert result == ParsedInternalUrl(namespace="ファイル", title="Flag.svg", fragment=None)


def test_unknown_colon_prefix_is_not_treated_as_namespace() -> None:
    result = parse_internal_url("/wiki/Vi_(text_editor):_notes", project_base_urls=_BASES)

    assert result is not None
    assert result.namespace is None
    assert result.title == "Vi (text editor): notes"


def test_external_url_returns_none() -> None:
    result = parse_internal_url("https://example.org/wiki/Emacs", project_base_urls=_BASES)

    assert result is None


def test_non_wiki_path_returns_none() -> None:
    result = parse_internal_url(
        "https://ja.wikipedia.org/w/index.php?title=Emacs", project_base_urls=_BASES
    )

    assert result is None


def test_bare_project_base_without_wiki_path_returns_none() -> None:
    result = parse_internal_url("https://ja.wikipedia.org/", project_base_urls=_BASES)

    assert result is None


def test_rejects_empty_url() -> None:
    with pytest.raises(UrlParseError, match="non-empty"):
        parse_internal_url("", project_base_urls=_BASES)
