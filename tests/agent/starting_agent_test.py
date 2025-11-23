from simple_agent.application.agent_type import AgentType
from simple_agent.application.session import SessionArgs
from simple_agent.infrastructure.configuration import get_starting_agent
from simple_agent.infrastructure.user_configuration import UserConfiguration, DEFAULT_STARTING_AGENT_TYPE


def test_defaults_to_orchestrator():
    user_config = UserConfiguration({})
    assert get_starting_agent(user_config) == AgentType(DEFAULT_STARTING_AGENT_TYPE)


def test_reads_starting_agent_from_config_section():
    user_config = UserConfiguration({"agents": {"start": "custom-root"}})

    assert get_starting_agent(user_config) == AgentType("custom-root")


def test_args_overwrites_config():
    user_config = UserConfiguration({"agents": {"start": "custom-root"}})

    assert get_starting_agent(user_config, SessionArgs(agent="from-args")) == AgentType("from-args")


def test_ignores_blank_values():
    user_config = UserConfiguration({"agents": {"start": "   "}})

    assert get_starting_agent(user_config) == AgentType(DEFAULT_STARTING_AGENT_TYPE)
