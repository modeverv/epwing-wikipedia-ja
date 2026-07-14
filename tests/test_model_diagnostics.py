from __future__ import annotations

import pytest

from wikiepwing.model.diagnostics import Diagnostic, DiagnosticError, parse_diagnostic


def _diagnostic(**overrides: object) -> Diagnostic:
    defaults: dict[str, object] = {
        "code": "DOM_UNKNOWN_ELEMENT",
        "severity": "warning",
        "stage": "normalize",
        "page_id": 123,
        "title": "Emacs",
        "message": "unknown element encountered",
        "source_path": "body/section[1]/p[2]",
        "source_excerpt": "<custom-tag>",
        "details": {"element_name": "custom-tag"},
    }
    defaults.update(overrides)
    return Diagnostic(**defaults)  # type: ignore[arg-type]


def test_constructs_valid_diagnostic() -> None:
    diagnostic = _diagnostic()

    assert diagnostic.code == "DOM_UNKNOWN_ELEMENT"
    assert diagnostic.severity == "warning"


def test_payload_round_trips_through_parse_diagnostic() -> None:
    diagnostic = _diagnostic()

    restored = parse_diagnostic(diagnostic.payload())

    assert restored == diagnostic


def test_payload_round_trips_with_null_optional_fields() -> None:
    diagnostic = _diagnostic(page_id=None, title=None, source_path=None, source_excerpt=None)

    restored = parse_diagnostic(diagnostic.payload())

    assert restored == diagnostic
    assert restored.page_id is None
    assert restored.title is None


def test_empty_code_is_rejected() -> None:
    with pytest.raises(DiagnosticError, match="code"):
        _diagnostic(code="")


def test_invalid_severity_is_rejected() -> None:
    with pytest.raises(DiagnosticError, match="severity"):
        _diagnostic(severity="ignored")


def test_empty_stage_is_rejected() -> None:
    with pytest.raises(DiagnosticError, match="stage"):
        _diagnostic(stage="")


def test_empty_message_is_rejected() -> None:
    with pytest.raises(DiagnosticError, match="message"):
        _diagnostic(message="")


def test_parse_rejects_non_object() -> None:
    with pytest.raises(DiagnosticError, match="JSON object"):
        parse_diagnostic(["not", "an", "object"])


def test_parse_rejects_missing_required_field() -> None:
    payload = _diagnostic().payload()
    del payload["message"]

    with pytest.raises(DiagnosticError, match="message"):
        parse_diagnostic(payload)


def test_parse_rejects_wrong_type_for_page_id() -> None:
    payload = _diagnostic().payload()
    payload["page_id"] = "not-an-int"

    with pytest.raises(DiagnosticError, match="page_id"):
        parse_diagnostic(payload)


def test_parse_rejects_wrong_type_for_details() -> None:
    payload = _diagnostic().payload()
    payload["details"] = "not-a-dict"

    with pytest.raises(DiagnosticError, match="details"):
        parse_diagnostic(payload)


def test_parse_rejects_boolean_page_id() -> None:
    payload = _diagnostic().payload()
    payload["page_id"] = True

    with pytest.raises(DiagnosticError, match="page_id"):
        parse_diagnostic(payload)
