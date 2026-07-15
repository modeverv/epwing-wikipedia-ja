from __future__ import annotations

from wikiepwing.model.article import MediaReference
from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.media_node import (
    is_figure_with_image,
    is_image_node,
    parse_figure_media,
    parse_image_node,
)


def _parse(html: str, tag: str) -> ElementNode:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=20)
    return _find(result.root, tag)


def _find(node: ElementNode, tag: str) -> ElementNode:
    found = _find_or_none(node, tag)
    if found is None:
        raise AssertionError(f"<{tag}> not found")
    return found


def _find_or_none(node: ElementNode, tag: str) -> ElementNode | None:
    if node.tag == tag:
        return node
    for child in node.children:
        if isinstance(child, ElementNode):
            found = _find_or_none(child, tag)
            if found is not None:
                return found
    return None


def test_recognizes_an_img_element() -> None:
    node = _parse('<img src="a.png">', "img")

    assert is_image_node(node) is True


def test_does_not_recognize_a_non_img_element() -> None:
    node = _parse("<span>x</span>", "span")

    assert is_image_node(node) is False


def test_extracts_media_reference_from_img() -> None:
    node = _parse(
        '<img src="https://example.org/wiki/Example.jpg" alt="an example" width="100" height="50">',
        "img",
    )

    media = parse_image_node(node)

    assert media == MediaReference(
        media_id="https://example.org/wiki/Example.jpg",
        source_url="https://example.org/wiki/Example.jpg",
        source_name="Example.jpg",
        alt_text="an example",
        caption=None,
        role="unknown",
        source_width=100,
        source_height=50,
    )


def test_url_decodes_source_name() -> None:
    node = _parse('<img src="https://example.org/wiki/My%20File.png">', "img")

    media = parse_image_node(node)

    assert media is not None
    assert media.source_name == "My File.png"


def test_missing_width_and_height_become_none() -> None:
    node = _parse('<img src="a.png">', "img")

    media = parse_image_node(node)

    assert media is not None
    assert media.source_width is None
    assert media.source_height is None


def test_invalid_width_becomes_none() -> None:
    node = _parse('<img src="a.png" width="not-a-number">', "img")

    media = parse_image_node(node)

    assert media is not None
    assert media.source_width is None


def test_negative_width_becomes_none() -> None:
    node = _parse('<img src="a.png" width="-5">', "img")

    media = parse_image_node(node)

    assert media is not None
    assert media.source_width is None


def test_missing_alt_becomes_none() -> None:
    node = _parse('<img src="a.png">', "img")

    media = parse_image_node(node)

    assert media is not None
    assert media.alt_text is None


def test_missing_src_returns_none() -> None:
    node = _parse("<img>", "img")

    media = parse_image_node(node)

    assert media is None


def test_parse_image_node_rejects_non_img_element() -> None:
    node = _parse("<span>x</span>", "span")

    try:
        parse_image_node(node)
        raise AssertionError("expected ValueError")
    except ValueError as error:
        assert "not an img element" in str(error)


def test_recognizes_figure_with_image() -> None:
    node = _parse('<figure><img src="a.png"><figcaption>caption</figcaption></figure>', "figure")

    assert is_figure_with_image(node) is True


def test_does_not_recognize_figure_without_image() -> None:
    node = _parse("<figure><figcaption>caption</figcaption></figure>", "figure")

    assert is_figure_with_image(node) is False


def test_parse_figure_media_uses_figcaption_as_caption() -> None:
    node = _parse(
        '<figure><img src="a.png" alt="alt"><figcaption>A caption</figcaption></figure>',
        "figure",
    )

    media = parse_figure_media(node)

    assert media is not None
    assert media.caption == "A caption"
    assert media.source_url == "a.png"


def test_parse_figure_media_without_figcaption_has_no_caption() -> None:
    node = _parse('<figure><img src="a.png"></figure>', "figure")

    media = parse_figure_media(node)

    assert media is not None
    assert media.caption is None


def test_parse_figure_media_without_image_returns_none() -> None:
    node = _parse("<figure><figcaption>caption</figcaption></figure>", "figure")

    media = parse_figure_media(node)

    assert media is None


def test_parse_figure_media_finds_nested_image() -> None:
    node = _parse(
        '<figure><a href="x"><img src="a.png"></a></figure>',
        "figure",
    )

    media = parse_figure_media(node)

    assert media is not None
    assert media.source_url == "a.png"
