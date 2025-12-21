import pytest

from simple_agent.infrastructure.configuration import (
    load_optional_user_configuration,
    load_user_configuration,
    resolve_api_key,
)


def test_resolve_api_key_replaces_env_placeholder(monkeypatch):
    monkeypatch.setenv("TEST_API_KEY", "secret-value")

    result = resolve_api_key("${TEST_API_KEY}")

    assert result == "secret-value"


def test_resolve_api_key_raises_when_env_missing():
    with pytest.raises(ValueError, match="environment variable 'MISSING_KEY' is not set"):
        resolve_api_key("${MISSING_KEY}")


def test_load_optional_user_configuration_resolves_api_key(monkeypatch, tmp_path):
    monkeypatch.setenv("NESTED_KEY", "nested-secret")
    home_dir = tmp_path / "home"
    cwd_dir = tmp_path / "cwd"
    home_dir.mkdir()
    cwd_dir.mkdir()
    monkeypatch.setenv("USERPROFILE", str(home_dir))
    monkeypatch.setenv("HOME", str(home_dir))

    config_path = cwd_dir / ".simple-agent.toml"
    config_path.write_text(
        "\n".join(
            [
                "[model]",
                'default = "claude"',
                "",
                "[models.claude]",
                'model = "claude-sonnet-4"',
                'adapter = "claude"',
                'api_key = "${NESTED_KEY}"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    user_config = load_optional_user_configuration(str(cwd_dir))
    registry = user_config.models_registry()

    assert registry.get("claude").api_key == "nested-secret"


def test_load_user_configuration_raises_when_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    with pytest.raises(FileNotFoundError, match=".simple-agent.toml not found"):
        load_user_configuration(str(tmp_path))


def test_resolve_api_key_returns_literal_when_not_placeholder():
    assert resolve_api_key("plain-key") == "plain-key"
