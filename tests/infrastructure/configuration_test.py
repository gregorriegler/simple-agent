import pytest

from simple_agent.infrastructure.user_configuration import UserConfiguration


def test_resolve_api_key_replaces_env_placeholder(monkeypatch, tmp_path):
    monkeypatch.setenv("TEST_API_KEY", "secret-value")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    config_path = tmp_path / ".simple-agent.toml"
    config_path.write_text(
        """
[model]
default = "primary"

[models.primary]
model = "test-model"
adapter = "test-adapter"
api_key = "${TEST_API_KEY}"
""".lstrip()
    )

    user_config = UserConfiguration.load_from_config_file(str(tmp_path))

    assert user_config.models_registry().get(None).api_key == "secret-value"


def test_resolve_api_key_raises_when_env_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    config_path = tmp_path / ".simple-agent.toml"
    config_path.write_text(
        """
[model]
default = "primary"

[models.primary]
model = "test-model"
adapter = "test-adapter"
api_key = "${MISSING_KEY}"
""".lstrip()
    )

    with pytest.raises(ValueError, match="environment variable 'MISSING_KEY' is not set"):
        UserConfiguration.load_from_config_file(str(tmp_path))


def test_load_user_configuration_raises_when_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    with pytest.raises(FileNotFoundError, match=".simple-agent.toml not found"):
        UserConfiguration.load_from_config_file(str(tmp_path))


def test_resolve_api_key_returns_literal_when_not_placeholder(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    config_path = tmp_path / ".simple-agent.toml"
    config_path.write_text(
        """
[model]
default = "primary"

[models.primary]
model = "test-model"
adapter = "test-adapter"
api_key = "plain-key"
""".lstrip()
    )

    user_config = UserConfiguration.load_from_config_file(str(tmp_path))

    assert user_config.models_registry().get(None).api_key == "plain-key"
