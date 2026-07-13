from __future__ import annotations

import io
import json
from pathlib import Path

from wikiepwing.logging import configure_logging


def test_writes_human_console_and_structured_jsonl(tmp_path: Path) -> None:
    console = io.StringIO()
    jsonl_path = tmp_path / "logs" / "build.jsonl"
    logger = configure_logging(
        level="INFO",
        run_id="run-001",
        stage="ingest",
        console_stream=console,
        jsonl_path=jsonl_path,
    )

    logger.info(
        event="article_rejected",
        message="article exceeded the configured limit",
        page_id=42,
        title="長い記事",
        diagnostic_code="SRC_HTML_TOO_LARGE",
    )
    logger.close()

    payload = json.loads(jsonl_path.read_text(encoding="utf-8"))
    assert payload == {
        "diagnostic_code": "SRC_HTML_TOO_LARGE",
        "event": "article_rejected",
        "level": "INFO",
        "message": "article exceeded the configured limit",
        "page_id": 42,
        "run_id": "run-001",
        "stage": "ingest",
        "timestamp": payload["timestamp"],
        "title": "長い記事",
    }
    assert payload["timestamp"].endswith("Z")
    assert "stage=ingest" in console.getvalue()
    assert "run_id=run-001" in console.getvalue()
    assert "article exceeded the configured limit" in console.getvalue()


def test_redacts_secrets_from_console_and_jsonl(tmp_path: Path) -> None:
    console = io.StringIO()
    jsonl_path = tmp_path / "build.jsonl"
    logger = configure_logging(
        level="INFO",
        run_id="run-secret",
        stage="source-acquire",
        console_stream=console,
        jsonl_path=jsonl_path,
        secrets=("configured-secret",),
    )

    logger.error(
        event="request_failed",
        message=(
            "configured-secret Authorization: Bearer bearer-secret "
            "password=password-secret access_token=access-secret"
        ),
        title="configured-secret",
        diagnostic_code="SRC_AUTH_FAILED",
    )
    logger.close()

    combined = console.getvalue() + jsonl_path.read_text(encoding="utf-8")
    for secret in (
        "configured-secret",
        "bearer-secret",
        "password-secret",
        "access-secret",
    ):
        assert secret not in combined
    assert "[REDACTED]" in combined


def test_bind_returns_logger_with_updated_context(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "build.jsonl"
    logger = configure_logging(
        level="INFO",
        run_id="run-002",
        stage="doctor",
        console_stream=io.StringIO(),
        jsonl_path=jsonl_path,
    )

    logger.bind(stage="normalize").info(event="stage_started", message="starting")
    logger.info(event="doctor_complete", message="complete")
    logger.close()

    payloads = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    assert [payload["stage"] for payload in payloads] == ["normalize", "doctor"]
