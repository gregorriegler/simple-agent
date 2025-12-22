import pytest

from simple_agent.infrastructure.configuration import (
    load_user_configuration,
    _resolve_api_key,
)


def test_resolve_api_key_replaces_env_placeholder(monkeypatch):
    monkeypatch.setenv("TEST_API_KEY", "secret-value")

    result = _resolve_api_key("${TEST_API_KEY}")

    assert result == "secret-value"


def test_resolve_api_key_raises_when_env_missing():
    with pytest.raises(ValueError, match="environment variable 'MISSING_KEY' is not set"):
        _resolve_api_key("${MISSING_KEY}")


def test_load_user_configuration_raises_when_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    with pytest.raises(FileNotFoundError, match=".simple-agent.toml not found"):
        load_user_configuration(str(tmp_path))


def test_resolve_api_key_returns_literal_when_not_placeholder():
    assert _resolve_api_key("plain-key") == "plain-key"
