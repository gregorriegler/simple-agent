import pytest
from simple_agent.infrastructure.model_config import ModelsRegistry, ModelConfig


def test_get_falls_back_to_default_model_when_unknown_model_requested():
    default_model = ModelConfig(
        name="claude",
        model="claude-sonnet-4",
        adapter="claude",
        api_key="test-key"
    )
    registry = ModelsRegistry(
        models={"claude": default_model},
        default="claude"
    )

    result = registry.get("non-existent-model")

    assert result == default_model
    assert result.name == "claude"



def test_get_prints_warning_to_stderr_when_falling_back(capsys):
    default_model = ModelConfig(
        name="claude",
        model="claude-sonnet-4",
        adapter="claude",
        api_key="test-key"
    )
    registry = ModelsRegistry(
        models={"claude": default_model},
        default="claude"
    )

    registry.get("unknown-model")

    captured = capsys.readouterr()
    assert "Warning: Unknown model configuration: 'unknown-model'" in captured.err
    assert "Falling back to default: 'claude'" in captured.err
    assert "Available models: claude" in captured.err


def test_get_returns_requested_model_when_it_exists():
    claude_model = ModelConfig(
        name="claude",
        model="claude-sonnet-4",
        adapter="claude",
        api_key="test-key-claude"
    )
    openai_model = ModelConfig(
        name="openai",
        model="gpt-4",
        adapter="openai",
        api_key="test-key-openai"
    )
    registry = ModelsRegistry(
        models={"claude": claude_model, "openai": openai_model},
        default="claude"
    )

    result = registry.get("openai")

    assert result == openai_model
    assert result.name == "openai"
