import pytest

from simple_agent.application.agent_type import AgentType


def test_cannot_be_empty():
    with pytest.raises(ValueError, match="Agent type cannot be empty"):
        AgentType("")


def test_cannot_be_whitespace():
    with pytest.raises(ValueError, match="Agent type cannot be empty"):
        AgentType("  ")


def test_raw_returns_type_name():
    assert AgentType("coding").raw == "coding"


def test_str_representation():
    assert str(AgentType("coding")) == "coding"


def test_repr_representation():
    assert repr(AgentType("coding")) == "AgentType('coding')"


def test_equality():
    assert AgentType("coding") == AgentType("coding")
    assert AgentType("coding") != AgentType("orchestrator")
    assert AgentType("coding") != "coding"


def test_hashable():
    agents = {AgentType("coding"), AgentType("coding"), AgentType("orchestrator")}
    assert len(agents) == 2
    assert AgentType("coding") in agents
