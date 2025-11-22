from simple_agent.infrastructure.configuration import (
    DEFAULT_STARTING_AGENT_TYPE,
    get_starting_agent_type,
)


def test_defaults_to_orchestrator():
    assert get_starting_agent_type({}) == DEFAULT_STARTING_AGENT_TYPE


def test_reads_starting_agent_from_config_section():
    config = {"agents": {"start": "custom-root"}}

    assert get_starting_agent_type(config) == "custom-root"


def test_ignores_blank_values():
    config = {"agents": {"start": "   "}}

    assert get_starting_agent_type(config) == DEFAULT_STARTING_AGENT_TYPE
