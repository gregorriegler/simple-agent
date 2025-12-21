from simple_agent.application.agent_types import AgentTypes


def test_empty_agent_types_is_false_and_length_zero():
    agent_types = AgentTypes.empty()

    assert bool(agent_types) is False
    assert len(agent_types) == 0


def test_agent_types_iterates_values_in_order():
    agent_types = AgentTypes(["orchestrator", "coding"])

    assert list(agent_types) == ["orchestrator", "coding"]


def test_agent_types_all_returns_list():
    agent_types = AgentTypes(["reviewer"])

    assert agent_types.all() == ["reviewer"]
