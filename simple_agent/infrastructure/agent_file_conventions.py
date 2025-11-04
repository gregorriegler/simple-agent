import os


def get_project_local_agents_dir() -> str:
    return os.path.join(os.getcwd(), ".simple-agent", "agents")


def agent_type_from_filename(filename: str) -> str:
    return filename.replace('.agent.md', '')


def filename_from_agent_type(agent_type: str) -> str:
    return f"{agent_type}.agent.md"