import glob
import os
from typing import Any

import yaml

from simple_agent.application.tool_library import ToolLibrary


def generate_system_prompt(filename: str, tool_library: ToolLibrary):
    template_content = _read_system_prompt_template(filename)
    tools_content = _generate_tools_content(tool_library)
    result = template_content.replace("{{DYNAMIC_TOOLS_PLACEHOLDER}}", tools_content)

    agents_content = _read_agents_content()
    return result + "\n\n" + agents_content


def extract_tool_keys_from_file(filename: str) -> list[str]:
    content = _load_agent_definitions_file(filename)
    return extract_tool_keys_from_prompt(content)


def extract_tool_keys_from_prompt(content: str) -> list[str]:
    metadata = extract_metadata(content)
    return _read_tool_keys(metadata.get('tools'))


def extract_metadata(content: str) -> dict[str, Any]:
    metadata, _ = _parse_front_matter(content)
    return metadata


def _read_system_prompt_template(filename):
    content = _load_agent_definitions_file(filename)
    return _strip_tool_keys_section(content)


def _strip_tool_keys_section(content: str) -> str:
    _, remainder = _parse_front_matter(content)
    return remainder


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


def _read_agents_content():
    try:
        agents_path = os.path.join(os.getcwd(), "AGENTS.md")
        with open(agents_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _generate_tools_content(tool_library: ToolLibrary):
    tools_lines = []

    for tool in tool_library.tools:
        tool_doc = _generate_tool_documentation(tool)
        tools_lines.append(tool_doc)

    return "\n\n".join(tools_lines)


def _generate_tool_documentation(tool):
    usage_info = tool.get_usage_info()
    lines = usage_info.split('\n')
    if not lines:
        return ""

    tool_line = lines[0]
    if not tool_line.startswith('Tool: '):
        return ""

    tool_name = tool_line.replace('Tool: ', '')

    description = ""
    for line in lines[1:]:
        if line.startswith('Description: '):
            description = line.replace('Description: ', '')
            break

    arguments = []
    in_arguments_section = False
    for line in lines:
        if line.strip() == "Arguments:":
            in_arguments_section = True
            continue
        elif in_arguments_section and line.strip().startswith("- "):
            arg = line.strip()[2:]
            arguments.append(arg)
        elif in_arguments_section and line.strip() == "":
            continue
        elif in_arguments_section and not line.strip().startswith("- ") and line.strip():
            break

    doc_lines = [f"## {tool_name}"]
    if description:
        doc_lines.append(f"{description}")

    remaining_lines = usage_info.split('\n')[2:]

    if tool_name == 'subagent':
        agent_types = _discover_agent_types()
        if agent_types:
            agent_types_list = ', '.join(f"'{t}'" for t in agent_types)
            injected_lines = []
            for line in remaining_lines:
                if 'agenttype:' in line.lower() and '{{AGENT_TYPES}}' in line:
                    injected_lines.append(
                        f" - agenttype: string (required) - Type of agent to create. Available types: {agent_types_list}"
                    )
                else:
                    injected_lines.append(line)
            remaining_lines = injected_lines

    if remaining_lines:
        doc_lines.extend(remaining_lines)

    return "\n".join(doc_lines)


def _discover_agent_types() -> list[str]:
    simple_agent_dir = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(simple_agent_dir, '*.agent.md')
    agent_files = glob.glob(pattern)
    agent_types = []
    for filepath in agent_files:
        basename = os.path.basename(filepath)
        agent_type = basename.replace('.agent.md', '')
        agent_types.append(agent_type)
    return sorted(agent_types)


def _load_agent_definitions_file(filename):
    content = ""
    try:
        from importlib import resources
        content = resources.read_text('simple_agent', filename)
    except FileNotFoundError:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    return content
