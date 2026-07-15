from __future__ import annotations

import pytest

from wikiepwing.media.svg_sanitizer import SvgSanitizeError, sanitize_svg


def test_safe_svg_is_preserved() -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>'

    result = sanitize_svg(svg)

    assert b"<rect" in result
    assert b'width="10"' in result


def test_rejects_doctype_declaration() -> None:
    svg = b'<?xml version="1.0"?><!DOCTYPE svg><svg xmlns="http://www.w3.org/2000/svg"/>'

    with pytest.raises(SvgSanitizeError, match="DOCTYPE"):
        sanitize_svg(svg)


def test_rejects_entity_declaration() -> None:
    svg = (
        b'<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        b'<svg xmlns="http://www.w3.org/2000/svg">&xxe;</svg>'
    )

    with pytest.raises(SvgSanitizeError, match="DOCTYPE"):
        sanitize_svg(svg)


def test_rejects_entity_declaration_case_insensitively() -> None:
    svg = b'<!doctype svg [<!entity xxe "x">]><svg xmlns="http://www.w3.org/2000/svg"/>'

    with pytest.raises(SvgSanitizeError):
        sanitize_svg(svg)


def test_rejects_malformed_xml() -> None:
    with pytest.raises(SvgSanitizeError, match="cannot parse"):
        sanitize_svg(b"<svg><unclosed></svg>")


def test_removes_script_element() -> None:
    svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg">'
        b'<script>alert(1)</script><rect width="1" height="1"/></svg>'
    )

    result = sanitize_svg(svg)

    assert b"script" not in result
    assert b"alert" not in result
    assert b"<rect" in result


def test_removes_foreign_object_element() -> None:
    svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg">'
        b'<foreignObject><div xmlns="http://www.w3.org/1999/xhtml">x</div></foreignObject>'
        b"</svg>"
    )

    result = sanitize_svg(svg)

    assert b"foreignObject" not in result


def test_removes_onload_event_handler() -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"><rect/></svg>'

    result = sanitize_svg(svg)

    assert b"onload" not in result
    assert b"alert" not in result


def test_removes_onclick_event_handler_case_insensitively() -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><rect OnClick="evil()"/></svg>'

    result = sanitize_svg(svg)

    assert b"onclick" not in result.lower()
    assert b"evil" not in result


def test_removes_javascript_href() -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><a href="javascript:alert(1)"><rect/></a></svg>'

    result = sanitize_svg(svg)

    assert b"javascript" not in result


def test_removes_javascript_xlink_href() -> None:
    svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg" '
        b'xmlns:xlink="http://www.w3.org/1999/xlink">'
        b'<a xlink:href=" JavaScript:alert(1)"><rect/></a></svg>'
    )

    result = sanitize_svg(svg)

    assert b"alert" not in result


def test_preserves_safe_href() -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><a href="#anchor"><rect/></a></svg>'

    result = sanitize_svg(svg)

    assert b'href="#anchor"' in result


def test_rejects_dangerous_root_element() -> None:
    with pytest.raises(SvgSanitizeError, match="root element"):
        sanitize_svg(b'<script xmlns="http://www.w3.org/2000/svg">alert(1)</script>')
