from __future__ import annotations

from wikiepwing.normalize.html_parser import ElementNode, parse_html
from wikiepwing.normalize.media_extraction import classify_body_media


def _body_children(html: str) -> tuple[ElementNode, ...]:
    result = parse_html(f"<html><body>{html}</body></html>", max_dom_depth=32)
    html_node = result.root.children[0]
    assert isinstance(html_node, ElementNode)
    body = html_node.children[0]
    assert isinstance(body, ElementNode)
    return body.children  # type: ignore[return-value]


def test_extracts_no_media_when_none_present() -> None:
    nodes = _body_children("<p>no images here</p>")

    result = classify_body_media(nodes)

    assert result == ()


def test_extracts_bare_img_element() -> None:
    nodes = _body_children('<p>text <img src="https://example.org/a.png"> more</p>')

    result = classify_body_media(nodes)

    assert len(result) == 1
    assert result[0].source_url == "https://example.org/a.png"


def test_extracts_figure_with_caption() -> None:
    nodes = _body_children(
        '<figure><img src="https://example.org/a.png"><figcaption>Caption text</figcaption>'
        "</figure>"
    )

    result = classify_body_media(nodes)

    assert len(result) == 1
    assert result[0].caption == "Caption text"


def test_figure_does_not_double_count_its_inner_img() -> None:
    nodes = _body_children('<figure><img src="https://example.org/a.png"></figure>')

    result = classify_body_media(nodes)

    assert len(result) == 1


def test_first_qualifying_image_becomes_lead() -> None:
    nodes = _body_children(
        '<p><img src="https://example.org/a.png"></p><p><img src="https://example.org/b.png"></p>'
    )

    result = classify_body_media(nodes)

    roles = {media.source_url: media.role for media in result}
    assert roles["https://example.org/a.png"] == "lead"
    assert roles["https://example.org/b.png"] == "body"


def test_infobox_images_are_classified_as_infobox_not_lead() -> None:
    nodes = _body_children(
        '<table class="infobox"><tr><td><img src="https://example.org/info.png"></td></tr>'
        "</table>"
        '<p><img src="https://example.org/body.png"></p>'
    )

    result = classify_body_media(nodes)

    roles = {media.source_url: media.role for media in result}
    assert roles["https://example.org/info.png"] == "infobox"
    assert roles["https://example.org/body.png"] == "lead"


def test_icon_sized_image_is_not_promoted_to_lead() -> None:
    nodes = _body_children(
        '<p><img src="https://example.org/icon.png" width="16" height="16"></p>'
        '<p><img src="https://example.org/real.png" width="400" height="300"></p>'
    )

    result = classify_body_media(nodes)

    roles = {media.source_url: media.role for media in result}
    assert roles["https://example.org/icon.png"] == "icon"
    assert roles["https://example.org/real.png"] == "lead"


def test_img_without_src_is_skipped() -> None:
    nodes = _body_children("<p><img></p>")

    result = classify_body_media(nodes)

    assert result == ()
