from simple_agent.application.agent_id import AgentId
from simple_agent.application.session import SessionArgs
from simple_agent.infrastructure.configuration import (
    DEFAULT_STARTING_AGENT_TYPE,
    get_starting_agent,
)


def test_defaults_to_orchestrator():
    assert get_starting_agent({}) == AgentId(DEFAULT_STARTING_AGENT_TYPE)


def test_reads_starting_agent_from_config_section():
    config = {"agents": {"start": "custom-root"}}

    assert get_starting_agent(config) == AgentId("custom-root")


def test_args_overwrites_config():
    config = {"agents": {"start": "custom-root"}}

    assert get_starting_agent(config, SessionArgs(agent="from-args")) == AgentId("from-args")


def test_ignores_blank_values():
    config = {"agents": {"start": "   "}}

    assert get_starting_agent(config) == AgentId(DEFAULT_STARTING_AGENT_TYPE)
