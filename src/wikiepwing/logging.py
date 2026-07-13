"""Human-readable and JSON Lines logging with mandatory build context."""

from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


@dataclass(frozen=True, slots=True)
class LogContext:
    """Stable context attached to every emitted event."""

    run_id: str
    stage: str


class _Redactor:
    _AUTHORIZATION = re.compile(
        r"(authorization\s*[:=]\s*)(?:bearer\s+)?([^\s,;]+)",
        re.IGNORECASE,
    )
    _NAMED_SECRET = re.compile(
        r"\b(password|access_token|refresh_token|id_token|token)\b"
        r"(\s*[:=]\s*)([^\s,;]+)",
        re.IGNORECASE,
    )

    def __init__(self, secrets: Iterable[str]) -> None:
        self._secrets = tuple(
            sorted({secret for secret in secrets if secret}, key=len, reverse=True)
        )

    def text(self, value: str) -> str:
        """Replace configured and recognizable credential values."""
        redacted = value
        for secret in self._secrets:
            redacted = redacted.replace(secret, "[REDACTED]")
        redacted = self._AUTHORIZATION.sub(r"\1[REDACTED]", redacted)
        return self._NAMED_SECRET.sub(r"\1\2[REDACTED]", redacted)

    def value(self, value: object) -> object:
        return self.text(value) if isinstance(value, str) else value


def _timestamp(record: logging.LogRecord) -> str:
    return (
        datetime.fromtimestamp(record.created, UTC)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _payload(record: logging.LogRecord, redactor: _Redactor) -> dict[str, object]:
    return {
        "timestamp": _timestamp(record),
        "level": record.levelname,
        "stage": redactor.value(record.__dict__.get("stage")),
        "run_id": redactor.value(record.__dict__.get("run_id")),
        "event": redactor.value(record.__dict__.get("event")),
        "page_id": record.__dict__.get("page_id"),
        "title": redactor.value(record.__dict__.get("title")),
        "diagnostic_code": redactor.value(record.__dict__.get("diagnostic_code")),
        "message": redactor.text(record.getMessage()),
    }


class JsonLinesFormatter(logging.Formatter):
    """Serialize one stable, redacted JSON object per log record."""

    def __init__(self, redactor: _Redactor) -> None:
        super().__init__()
        self._redactor = redactor

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            _payload(record, self._redactor),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


class ConsoleFormatter(logging.Formatter):
    """Render redacted event fields in a compact human-readable form."""

    def __init__(self, redactor: _Redactor) -> None:
        super().__init__()
        self._redactor = redactor

    def format(self, record: logging.LogRecord) -> str:
        payload = _payload(record, self._redactor)
        return (
            f"{payload['timestamp']} {payload['level']} "
            f"stage={payload['stage']} run_id={payload['run_id']} "
            f"event={payload['event']} page_id={payload['page_id']} "
            f"title={payload['title']} diagnostic_code={payload['diagnostic_code']} "
            f"{payload['message']}"
        )


@dataclass(frozen=True, slots=True)
class StructuredLogger:
    """Emit pipeline events with immutable stage and run context."""

    _logger: logging.Logger
    context: LogContext

    def bind(self, *, run_id: str | None = None, stage: str | None = None) -> StructuredLogger:
        """Return a view sharing handlers but carrying updated context."""
        return StructuredLogger(
            self._logger,
            LogContext(
                run_id=_require_context("run_id", run_id or self.context.run_id),
                stage=_require_context("stage", stage or self.context.stage),
            ),
        )

    def debug(
        self,
        *,
        event: str,
        message: str,
        page_id: int | None = None,
        title: str | None = None,
        diagnostic_code: str | None = None,
    ) -> None:
        """Emit a DEBUG event."""
        self._emit(logging.DEBUG, event, message, page_id, title, diagnostic_code)

    def info(
        self,
        *,
        event: str,
        message: str,
        page_id: int | None = None,
        title: str | None = None,
        diagnostic_code: str | None = None,
    ) -> None:
        """Emit an INFO event."""
        self._emit(logging.INFO, event, message, page_id, title, diagnostic_code)

    def warning(
        self,
        *,
        event: str,
        message: str,
        page_id: int | None = None,
        title: str | None = None,
        diagnostic_code: str | None = None,
    ) -> None:
        """Emit a WARNING event."""
        self._emit(logging.WARNING, event, message, page_id, title, diagnostic_code)

    def error(
        self,
        *,
        event: str,
        message: str,
        page_id: int | None = None,
        title: str | None = None,
        diagnostic_code: str | None = None,
    ) -> None:
        """Emit an ERROR event."""
        self._emit(logging.ERROR, event, message, page_id, title, diagnostic_code)

    def critical(
        self,
        *,
        event: str,
        message: str,
        page_id: int | None = None,
        title: str | None = None,
        diagnostic_code: str | None = None,
    ) -> None:
        """Emit a CRITICAL event."""
        self._emit(logging.CRITICAL, event, message, page_id, title, diagnostic_code)

    def _emit(
        self,
        level: int,
        event: str,
        message: str,
        page_id: int | None,
        title: str | None,
        diagnostic_code: str | None,
    ) -> None:
        self._logger.log(
            level,
            message,
            extra={
                "stage": self.context.stage,
                "run_id": self.context.run_id,
                "event": _require_context("event", event),
                "page_id": page_id,
                "title": title,
                "diagnostic_code": diagnostic_code,
            },
        )

    def close(self) -> None:
        """Flush, close, and detach every configured output handler."""
        for handler in tuple(self._logger.handlers):
            handler.flush()
            handler.close()
            self._logger.removeHandler(handler)


def _require_context(name: str, value: str) -> str:
    if not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def configure_logging(
    *,
    level: str,
    run_id: str,
    stage: str,
    jsonl_path: Path | None = None,
    console_stream: TextIO | None = None,
    secrets: Iterable[str] = (),
) -> StructuredLogger:
    """Create isolated console and optional JSON Lines logging outputs."""
    normalized_level = level.upper()
    if normalized_level not in _LEVELS:
        raise ValueError(f"unsupported log level: {level}")

    redactor = _Redactor(secrets)
    logger = logging.Logger("wikiepwing", level=_LEVELS[normalized_level])
    logger.propagate = False

    console_handler = logging.StreamHandler(console_stream or sys.stderr)
    console_handler.setFormatter(ConsoleFormatter(redactor))
    logger.addHandler(console_handler)

    if jsonl_path is not None:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        jsonl_handler = logging.FileHandler(jsonl_path, encoding="utf-8")
        jsonl_handler.setFormatter(JsonLinesFormatter(redactor))
        logger.addHandler(jsonl_handler)

    return StructuredLogger(
        logger,
        LogContext(
            run_id=_require_context("run_id", run_id),
            stage=_require_context("stage", stage),
        ),
    )
