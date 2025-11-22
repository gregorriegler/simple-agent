import os

from simple_agent.application.agent_id import AgentId


def get_project_local_agents_dir(base_dir: str) -> str:
    return os.path.join(base_dir, ".simple-agent", "agents")


def agent_type_from_filename(filename: str) -> str:
    return filename.replace('.agent.md', '')


def filename_from_agent_type(agent_id: AgentId) -> str:
    return f"{agent_id.for_filesystem()}.agent.md"
