from simple_agent.application.agent_type import AgentType
from simple_agent.application.session import SessionArgs
from simple_agent.infrastructure.configuration import (
    DEFAULT_STARTING_AGENT_TYPE,
    get_starting_agent,
)


def test_defaults_to_orchestrator():
    assert get_starting_agent({}) == AgentType(DEFAULT_STARTING_AGENT_TYPE)


def test_reads_starting_agent_from_config_section():
    config = {"agents": {"start": "custom-root"}}

    assert get_starting_agent(config) == AgentType("custom-root")


def test_args_overwrites_config():
    config = {"agents": {"start": "custom-root"}}

    assert get_starting_agent(config, SessionArgs(agent="from-args")) == AgentType("from-args")


def test_ignores_blank_values():
    config = {"agents": {"start": "   "}}

    assert get_starting_agent(config) == AgentType(DEFAULT_STARTING_AGENT_TYPE)
