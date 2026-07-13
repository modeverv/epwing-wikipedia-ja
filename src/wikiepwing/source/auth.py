"""Enterprise authentication: fixed access/refresh/login priority, no persistence."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol, cast

from wikiepwing.secrets import EnterpriseSecrets

DEFAULT_AUTH_TIMEOUT_SECONDS = 30.0
MAX_AUTH_RESPONSE_BYTES = 64 * 1024


class AuthError(RuntimeError):
    """Raised when enterprise authentication cannot resolve a usable access token."""


@dataclass(frozen=True, slots=True)
class ResolvedAccessToken:
    """An access token resolved for one run; held in memory only."""

    value: str
    source: str

    def redaction_values(self) -> tuple[str, ...]:
        """Return this token for structured-log redaction."""
        return (self.value,)


class AuthTransport(Protocol):
    """Network operations required to exchange credentials for an access token."""

    def refresh(self, refresh_token: str, *, timeout_seconds: float) -> str: ...

    def login(self, username: str, password: str, *, timeout_seconds: float) -> str: ...


class EnterpriseAuthClient:
    """Resolve one usable access token per the fixed priority order."""

    def __init__(
        self,
        transport: AuthTransport,
        *,
        timeout_seconds: float = DEFAULT_AUTH_TIMEOUT_SECONDS,
    ) -> None:
        if timeout_seconds <= 0:
            raise AuthError("auth timeout_seconds must be positive")
        self._transport = transport
        self._timeout_seconds = timeout_seconds

    def resolve(self, secrets: EnterpriseSecrets) -> ResolvedAccessToken:
        """Return the first usable credential: access token, then refresh, then login."""
        if secrets.access_token is not None:
            return ResolvedAccessToken(secrets.access_token, "access_token")
        if secrets.refresh_token is not None:
            value = self._transport.refresh(
                secrets.refresh_token, timeout_seconds=self._timeout_seconds
            )
            return ResolvedAccessToken(_require_non_empty(value), "refresh_token")
        if secrets.username is not None and secrets.password is not None:
            value = self._transport.login(
                secrets.username, secrets.password, timeout_seconds=self._timeout_seconds
            )
            return ResolvedAccessToken(_require_non_empty(value), "login")
        raise AuthError(
            "no enterprise credentials available: set WME_ACCESS_TOKEN, WME_REFRESH_TOKEN, "
            "or WME_USERNAME and WME_PASSWORD"
        )


def _require_non_empty(value: str) -> str:
    if not value:
        raise AuthError("enterprise auth transport returned an empty access token")
    return value


class _AuthResponse(Protocol):
    """The subset of an HTTP response this transport relies on."""

    status: int

    def read(self, limit: int) -> bytes: ...


class HttpAuthTransport:
    """Bounded HTTPS auth transport for the Wikimedia Enterprise auth API."""

    def __init__(
        self,
        base_url: str,
        *,
        opener: Callable[..., AbstractContextManager[_AuthResponse]] = urllib.request.urlopen,
        max_response_bytes: int = MAX_AUTH_RESPONSE_BYTES,
    ) -> None:
        if not base_url.startswith("https://"):
            raise AuthError("enterprise auth base URL must use https://")
        if max_response_bytes < 1:
            raise AuthError("max_response_bytes must be positive")
        self._base_url = base_url.rstrip("/")
        self._opener = opener
        self._max_response_bytes = max_response_bytes

    def refresh(self, refresh_token: str, *, timeout_seconds: float) -> str:
        """Exchange a refresh token for a new access token."""
        return self._exchange("/token-refresh", {"refresh_token": refresh_token}, timeout_seconds)

    def login(self, username: str, password: str, *, timeout_seconds: float) -> str:
        """Exchange a username/password pair for a new access token."""
        return self._exchange(
            "/login", {"username": username, "password": password}, timeout_seconds
        )

    def _exchange(self, path: str, body: dict[str, str], timeout_seconds: float) -> str:
        if timeout_seconds <= 0:
            raise AuthError("auth timeout_seconds must be positive")
        request = urllib.request.Request(
            f"{self._base_url}{path}",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(request, timeout=timeout_seconds) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read(self._max_response_bytes + 1)
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise AuthError(
                    f"enterprise auth rejected credentials: HTTP {error.code}"
                ) from error
            raise AuthError(f"enterprise auth request failed: HTTP {error.code}") from error
        except urllib.error.URLError as error:
            raise AuthError(f"enterprise auth request failed: {error.reason}") from error
        except TimeoutError as error:
            raise AuthError(
                f"enterprise auth request timed out after {timeout_seconds:g} seconds"
            ) from error

        if len(raw) > self._max_response_bytes:
            raise AuthError(f"enterprise auth response exceeded {self._max_response_bytes} bytes")
        if status >= 400:
            raise AuthError(f"enterprise auth request failed: HTTP {status}")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AuthError(f"enterprise auth response was not valid JSON: {error}") from error
        if not isinstance(payload, dict) or not isinstance(payload.get("access_token"), str):
            raise AuthError("enterprise auth response is missing a string access_token")
        return cast(str, payload["access_token"])
