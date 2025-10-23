import os
from typing import Any

import yaml

from simple_agent.application.system_prompt import AgentPrompt


def extract_tool_keys(agent_type: str) -> list[str]:
    prompt = load_agent_prompt(agent_type)
    return prompt.tool_keys


def load_agent_prompt(agent_type: str) -> AgentPrompt:
    filename = _system_prompt_filename(agent_type)
    content = _load_agent_definitions_file(filename)
    metadata, template = _parse_front_matter(content)
    tool_keys = _read_tool_keys(metadata.get('tools'))
    agents_content = _read_agents_content()
    return AgentPrompt(template, tool_keys, agents_content)


def extract_tool_keys_from_prompt(content: str) -> list[str]:
    metadata = extract_metadata(content)
    return _read_tool_keys(metadata.get('tools'))


def extract_metadata(content: str) -> dict[str, Any]:
    metadata, _ = _parse_front_matter(content)
    return metadata


def _system_prompt_filename(agent_type: str) -> str:
    return f"{agent_type}.agent.md"


def _parse_front_matter(content: str) -> tuple[dict[str, Any], str]:
    if not content:
        return {}, content

    leading_trimmed = content.lstrip()
    leading_prefix = content[: len(content) - len(leading_trimmed)]
    working = leading_trimmed

    if not working.startswith('---'):
        return {}, content

    working = working[3:]

    if working.startswith('\r\n'):
        newline = '\r\n'
        working = working[2:]
    elif working.startswith('\n'):
        newline = '\n'
        working = working[1:]
    else:
        return {}, content

    closing = f"{newline}---"
    end_index = working.find(closing)
    if end_index == -1:
        return {}, content

    front_matter_text = working[:end_index]
    remainder = working[end_index + len(closing):]
    if newline and remainder.startswith(newline):
        remainder = remainder[len(newline):]

    metadata = _load_front_matter(front_matter_text)
    return metadata, leading_prefix + remainder


def _load_front_matter(front_matter_text: str) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(front_matter_text) or {}
    except yaml.YAMLError:
        return {}

    if isinstance(loaded, dict):
        return loaded

    return {}


def _read_tool_keys(raw_tools: Any) -> list[str]:
    if raw_tools is None:
        return []

    if isinstance(raw_tools, str):
        parts = [item.strip() for item in raw_tools.split(',')]
        return [item for item in parts if item]

    if isinstance(raw_tools, list):
        normalized = []
        for item in raw_tools:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    normalized.append(stripped)
        return normalized

    return []


def _read_agents_content() -> str:
    try:
        agents_path = os.path.join(os.getcwd(), "AGENTS.md")
        with open(agents_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _load_agent_definitions_file(filename: str) -> str:
    try:
        from importlib import resources
        return resources.read_text('simple_agent', filename)
    except FileNotFoundError:
        package_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        filepath = os.path.join(package_root, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
