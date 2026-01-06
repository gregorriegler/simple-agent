from simple_agent.application.agent_type import AgentType
from simple_agent.application.session import SessionArgs
from simple_agent.infrastructure.user_configuration import UserConfiguration


def get_starting_agent(
    user_config: UserConfiguration, args: SessionArgs | None = None
) -> AgentType:
    if args and args.stub_llm:
        return UserConfiguration.default_starting_agent_type()
    if args and args.agent:
        return AgentType(args.agent)
    return user_config.starting_agent_type()
