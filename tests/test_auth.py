from __future__ import annotations

import json
import urllib.error
from typing import Any

import pytest

from wikiepwing.secrets import EnterpriseSecrets
from wikiepwing.source.auth import (
    AuthError,
    EnterpriseAuthClient,
    HttpAuthTransport,
    ResolvedAccessToken,
)


class _RaisingTransport:
    def refresh(self, refresh_token: str, *, timeout_seconds: float) -> str:
        raise AssertionError("refresh must not be called when an access token is present")

    def login(self, username: str, password: str, *, timeout_seconds: float) -> str:
        raise AssertionError("login must not be called when an access token is present")


class _RecordingTransport:
    def __init__(
        self, *, refresh_result: str = "refreshed", login_result: str = "logged-in"
    ) -> None:
        self.refresh_calls: list[tuple[str, float]] = []
        self.login_calls: list[tuple[str, str, float]] = []
        self._refresh_result = refresh_result
        self._login_result = login_result

    def refresh(self, refresh_token: str, *, timeout_seconds: float) -> str:
        self.refresh_calls.append((refresh_token, timeout_seconds))
        return self._refresh_result

    def login(self, username: str, password: str, *, timeout_seconds: float) -> str:
        self.login_calls.append((username, password, timeout_seconds))
        return self._login_result


def test_access_token_present_bypasses_transport() -> None:
    client = EnterpriseAuthClient(_RaisingTransport())
    secrets = EnterpriseSecrets(
        username=None, password=None, access_token="abc123", refresh_token=None
    )

    resolved = client.resolve(secrets)

    assert resolved == ResolvedAccessToken("abc123", "access_token")
    assert resolved.redaction_values() == ("abc123",)


def test_refresh_token_used_when_no_access_token() -> None:
    transport = _RecordingTransport()
    client = EnterpriseAuthClient(transport, timeout_seconds=5.0)
    secrets = EnterpriseSecrets(
        username=None, password=None, access_token=None, refresh_token="refresh-xyz"
    )

    resolved = client.resolve(secrets)

    assert resolved == ResolvedAccessToken("refreshed", "refresh_token")
    assert transport.refresh_calls == [("refresh-xyz", 5.0)]
    assert transport.login_calls == []


def test_login_used_when_only_username_password_present() -> None:
    transport = _RecordingTransport()
    client = EnterpriseAuthClient(transport, timeout_seconds=7.0)
    secrets = EnterpriseSecrets(
        username="alice", password="hunter2", access_token=None, refresh_token=None
    )

    resolved = client.resolve(secrets)

    assert resolved == ResolvedAccessToken("logged-in", "login")
    assert transport.login_calls == [("alice", "hunter2", 7.0)]


def test_refresh_token_takes_priority_over_login() -> None:
    transport = _RecordingTransport()
    client = EnterpriseAuthClient(transport)
    secrets = EnterpriseSecrets(
        username="alice", password="hunter2", access_token=None, refresh_token="refresh-xyz"
    )

    resolved = client.resolve(secrets)

    assert resolved.source == "refresh_token"
    assert transport.login_calls == []


def test_missing_credentials_raises() -> None:
    client = EnterpriseAuthClient(_RaisingTransport())
    secrets = EnterpriseSecrets(username=None, password=None, access_token=None, refresh_token=None)

    with pytest.raises(AuthError):
        client.resolve(secrets)


def test_transport_returning_empty_token_is_rejected() -> None:
    transport = _RecordingTransport(refresh_result="")
    client = EnterpriseAuthClient(transport)
    secrets = EnterpriseSecrets(
        username=None, password=None, access_token=None, refresh_token="refresh-xyz"
    )

    with pytest.raises(AuthError):
        client.resolve(secrets)


def test_non_positive_timeout_is_rejected() -> None:
    with pytest.raises(AuthError):
        EnterpriseAuthClient(_RaisingTransport(), timeout_seconds=0)


class _FakeResponse:
    def __init__(self, *, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self._body


def _opener_returning(status: int, payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")

    def opener(request: Any, timeout: float) -> _FakeResponse:
        assert timeout > 0
        return _FakeResponse(status=status, body=body)

    return opener


def test_http_transport_login_success() -> None:
    transport = HttpAuthTransport(
        "https://auth.enterprise.wikimedia.com/v1",
        opener=_opener_returning(200, {"access_token": "issued-token"}),
    )

    assert transport.login("alice", "hunter2", timeout_seconds=5.0) == "issued-token"


def test_http_transport_refresh_success() -> None:
    transport = HttpAuthTransport(
        "https://auth.enterprise.wikimedia.com/v1",
        opener=_opener_returning(200, {"access_token": "refreshed-token"}),
    )

    assert transport.refresh("refresh-xyz", timeout_seconds=5.0) == "refreshed-token"


def test_http_transport_requires_https() -> None:
    with pytest.raises(AuthError):
        HttpAuthTransport("http://auth.enterprise.wikimedia.com/v1")


def test_http_transport_401_raises_immediately() -> None:
    def opener(request: Any, timeout: float) -> Any:
        raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", None, None)

    transport = HttpAuthTransport("https://auth.enterprise.wikimedia.com/v1", opener=opener)

    with pytest.raises(AuthError, match="401"):
        transport.login("alice", "wrong-password", timeout_seconds=5.0)


def test_http_transport_5xx_raises() -> None:
    def opener(request: Any, timeout: float) -> Any:
        raise urllib.error.HTTPError(request.full_url, 503, "unavailable", None, None)

    transport = HttpAuthTransport("https://auth.enterprise.wikimedia.com/v1", opener=opener)

    with pytest.raises(AuthError, match="503"):
        transport.refresh("refresh-xyz", timeout_seconds=5.0)


def test_http_transport_timeout_raises() -> None:
    def opener(request: Any, timeout: float) -> Any:
        raise TimeoutError("timed out")

    transport = HttpAuthTransport("https://auth.enterprise.wikimedia.com/v1", opener=opener)

    with pytest.raises(AuthError, match="timed out"):
        transport.login("alice", "hunter2", timeout_seconds=1.0)


def test_http_transport_oversized_response_is_rejected() -> None:
    transport = HttpAuthTransport(
        "https://auth.enterprise.wikimedia.com/v1",
        opener=_opener_returning(200, {"access_token": "x" * 200}),
        max_response_bytes=16,
    )

    with pytest.raises(AuthError, match="exceeded"):
        transport.login("alice", "hunter2", timeout_seconds=5.0)


def test_http_transport_malformed_json_is_rejected() -> None:
    def opener(request: Any, timeout: float) -> _FakeResponse:
        return _FakeResponse(status=200, body=b"not json")

    transport = HttpAuthTransport("https://auth.enterprise.wikimedia.com/v1", opener=opener)

    with pytest.raises(AuthError, match="not valid JSON"):
        transport.login("alice", "hunter2", timeout_seconds=5.0)


def test_http_transport_missing_access_token_field_is_rejected() -> None:
    transport = HttpAuthTransport(
        "https://auth.enterprise.wikimedia.com/v1",
        opener=_opener_returning(200, {"id_token": "irrelevant"}),
    )

    with pytest.raises(AuthError, match="missing"):
        transport.login("alice", "hunter2", timeout_seconds=5.0)


def test_http_transport_non_positive_timeout_is_rejected() -> None:
    transport = HttpAuthTransport(
        "https://auth.enterprise.wikimedia.com/v1",
        opener=_opener_returning(200, {"access_token": "x"}),
    )

    with pytest.raises(AuthError):
        transport.login("alice", "hunter2", timeout_seconds=0)
