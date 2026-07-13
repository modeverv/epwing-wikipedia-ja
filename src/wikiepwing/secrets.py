"""Enterprise credential environment variables: names, loading, validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

USERNAME_VAR = "WME_USERNAME"
PASSWORD_VAR = "WME_PASSWORD"
ACCESS_TOKEN_VAR = "WME_ACCESS_TOKEN"
REFRESH_TOKEN_VAR = "WME_REFRESH_TOKEN"

SECRET_ENVIRONMENT_VARIABLES = (
    USERNAME_VAR,
    PASSWORD_VAR,
    ACCESS_TOKEN_VAR,
    REFRESH_TOKEN_VAR,
)


class SecretError(ValueError):
    """Raised when enterprise credential environment variables are invalid."""


@dataclass(frozen=True, slots=True)
class EnterpriseSecrets:
    """Enterprise credentials read from the process environment, never persisted."""

    username: str | None
    password: str | None
    access_token: str | None
    refresh_token: str | None

    def redaction_values(self) -> tuple[str, ...]:
        """Return every non-empty secret value for log redaction."""
        return tuple(
            value
            for value in (self.username, self.password, self.access_token, self.refresh_token)
            if value is not None
        )


def load_enterprise_secrets(environ: Mapping[str, str]) -> EnterpriseSecrets:
    """Read, validate, and return enterprise credentials without persisting them."""
    username = _read_variable(environ, USERNAME_VAR)
    password = _read_variable(environ, PASSWORD_VAR)
    access_token = _read_variable(environ, ACCESS_TOKEN_VAR)
    refresh_token = _read_variable(environ, REFRESH_TOKEN_VAR)

    if (username is None) != (password is None):
        raise SecretError(f"{USERNAME_VAR} and {PASSWORD_VAR} must be set together or not at all")

    return EnterpriseSecrets(
        username=username,
        password=password,
        access_token=access_token,
        refresh_token=refresh_token,
    )


def _read_variable(environ: Mapping[str, str], name: str) -> str | None:
    raw = environ.get(name)
    if raw is None or raw == "":
        return None
    if raw.strip() != raw or raw.strip() == "":
        raise SecretError(f"{name} must not have leading, trailing, or only whitespace")
    if any(character in raw for character in ("\n", "\r", "\t")):
        raise SecretError(f"{name} must not contain control characters")
    return raw
