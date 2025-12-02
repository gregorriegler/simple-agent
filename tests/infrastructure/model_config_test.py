import pytest
from simple_agent.infrastructure.model_config import ModelsRegistry, ModelConfig


def test_get_falls_back_to_default_model_when_unknown_model_requested():
    """
    When get() is called with an unknown model name,
    it should return the default model instead of calling sys.exit(1)
    """
    # Given a ModelsRegistry with a default model
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
    
    # When get() is called with a non-existent model name
    result = registry.get("non-existent-model")
    
    # Then it should return the default model
    assert result == default_model
    assert result.name == "claude"