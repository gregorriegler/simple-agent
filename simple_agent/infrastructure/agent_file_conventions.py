from simple_agent.application.agent_type import AgentType


def agent_type_from_filename(filename: str) -> str:
    return filename.replace(".agent.md", "")


def filename_from_agent_type(agent_type: AgentType) -> str:
    return f"{agent_type.raw}.agent.md"
