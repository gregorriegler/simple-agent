import pytest

from simple_agent.infrastructure.model_config import ModelConfig, ModelsRegistry


def test_get_falls_back_to_default_model_when_unknown_model_requested():
    default_model = ModelConfig(
        name="claude", model="claude-sonnet-4", adapter="claude", api_key="test-key"
    )
    registry = ModelsRegistry(models={"claude": default_model}, default="claude")

    result = registry.get("non-existent-model")

    assert result == default_model
    assert result.name == "claude"


def test_get_does_not_emit_warning_when_falling_back(capsys):
    default_model = ModelConfig(
        name="claude", model="claude-sonnet-4", adapter="claude", api_key="test-key"
    )
    registry = ModelsRegistry(models={"claude": default_model}, default="claude")

    registry.get("unknown-model")

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_get_returns_requested_model_when_it_exists():
    claude_model = ModelConfig(
        name="claude",
        model="claude-sonnet-4",
        adapter="claude",
        api_key="test-key-claude",
    )
    openai_model = ModelConfig(
        name="openai", model="gpt-4", adapter="openai", api_key="test-key-openai"
    )
    registry = ModelsRegistry(
        models={"claude": claude_model, "openai": openai_model}, default="claude"
    )

    result = registry.get("openai")

    assert result == openai_model
    assert result.name == "openai"


def test_model_config_from_dict_requires_model_field():
    with pytest.raises(ValueError, match="missing required field 'model'"):
        ModelConfig.from_dict("claude", {"adapter": "claude", "api_key": "key"})


def test_model_config_from_dict_normalizes_adapter_and_timeout():
    config = {
        "model": "claude-sonnet-4",
        "adapter": "Claude",
        "api_key": "key",
        "request_timeout": "30",
    }

    model = ModelConfig.from_dict("claude", config)

    assert model.adapter == "claude"
    assert model.request_timeout == 30


def test_model_config_from_dict_raises_on_invalid_timeout():
    config = {
        "model": "claude-sonnet-4",
        "adapter": "claude",
        "api_key": "key",
        "request_timeout": "invalid",
    }

    with pytest.raises(ValueError, match="non-integer 'request_timeout'"):
        ModelConfig.from_dict("claude", config)


def test_models_registry_from_config_builds_registry():
    config = {
        "model": {"default": "claude"},
        "models": {
            "claude": {
                "model": "claude-sonnet-4",
                "adapter": "claude",
                "api_key": "key",
            },
            "openai": {
                "model": "gpt-4",
                "adapter": "openai",
                "api_key": "key",
            },
        },
    }

    registry = ModelsRegistry.from_config(config)

    assert registry.default == "claude"
    assert registry.get("openai").adapter == "openai"


def test_models_registry_from_config_requires_default_model():
    config = {
        "model": {},
        "models": {
            "claude": {
                "model": "claude-sonnet-4",
                "adapter": "claude",
                "api_key": "key",
            }
        },
    }

    with pytest.raises(ValueError, match="model.default"):
        ModelsRegistry.from_config(config)


def test_models_registry_from_config_requires_models_section():
    config = {"model": {"default": "claude"}}

    with pytest.raises(ValueError, match="models' section"):
        ModelsRegistry.from_config(config)


def test_models_registry_from_config_requires_default_in_models():
    config = {
        "model": {"default": "claude"},
        "models": {
            "openai": {
                "model": "gpt-4",
                "adapter": "openai",
                "api_key": "key",
            }
        },
    }

    with pytest.raises(ValueError, match="default model 'claude' not found"):
        ModelsRegistry.from_config(config)
