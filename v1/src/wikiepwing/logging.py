"""Small JSON logging adapter used by pipeline stages."""

from __future__ import annotations

import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit stable structured log records without article content."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        stage = getattr(record, "stage", None)
        if stage is not None:
            payload["stage"] = stage
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def configure_logging(level: str) -> None:
    """Configure process-wide structured logging exactly once per invocation."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
