from __future__ import annotations

import pytest

from wikiepwing.secrets import (
    ACCESS_TOKEN_VAR,
    PASSWORD_VAR,
    REFRESH_TOKEN_VAR,
    SECRET_ENVIRONMENT_VARIABLES,
    USERNAME_VAR,
    SecretError,
    load_enterprise_secrets,
)


def test_no_environment_variables_yield_all_none() -> None:
    secrets = load_enterprise_secrets({})

    assert secrets.username is None
    assert secrets.password is None
    assert secrets.access_token is None
    assert secrets.refresh_token is None
    assert secrets.redaction_values() == ()


def test_access_token_alone_is_valid() -> None:
    secrets = load_enterprise_secrets({ACCESS_TOKEN_VAR: "abc123"})

    assert secrets.access_token == "abc123"
    assert secrets.redaction_values() == ("abc123",)


def test_refresh_token_alone_is_valid() -> None:
    secrets = load_enterprise_secrets({REFRESH_TOKEN_VAR: "refresh-xyz"})

    assert secrets.refresh_token == "refresh-xyz"


def test_username_and_password_together_is_valid() -> None:
    secrets = load_enterprise_secrets({USERNAME_VAR: "alice", PASSWORD_VAR: "hunter2"})

    assert secrets.username == "alice"
    assert secrets.password == "hunter2"
    assert secrets.redaction_values() == ("alice", "hunter2")


def test_username_without_password_is_rejected() -> None:
    with pytest.raises(SecretError):
        load_enterprise_secrets({USERNAME_VAR: "alice"})


def test_password_without_username_is_rejected() -> None:
    with pytest.raises(SecretError):
        load_enterprise_secrets({PASSWORD_VAR: "hunter2"})


def test_empty_string_is_treated_as_absent() -> None:
    secrets = load_enterprise_secrets({ACCESS_TOKEN_VAR: ""})

    assert secrets.access_token is None


def test_whitespace_only_value_is_rejected() -> None:
    with pytest.raises(SecretError):
        load_enterprise_secrets({ACCESS_TOKEN_VAR: "   "})


def test_leading_or_trailing_whitespace_is_rejected() -> None:
    with pytest.raises(SecretError):
        load_enterprise_secrets({ACCESS_TOKEN_VAR: " abc123"})


def test_control_character_is_rejected() -> None:
    with pytest.raises(SecretError):
        load_enterprise_secrets({ACCESS_TOKEN_VAR: "abc\ndef"})


def test_secret_environment_variable_names_are_stable() -> None:
    assert SECRET_ENVIRONMENT_VARIABLES == (
        USERNAME_VAR,
        PASSWORD_VAR,
        ACCESS_TOKEN_VAR,
        REFRESH_TOKEN_VAR,
    )
    assert USERNAME_VAR == "WME_USERNAME"
    assert PASSWORD_VAR == "WME_PASSWORD"
    assert ACCESS_TOKEN_VAR == "WME_ACCESS_TOKEN"
    assert REFRESH_TOKEN_VAR == "WME_REFRESH_TOKEN"
