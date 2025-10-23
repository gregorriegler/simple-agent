from typing import Protocol


class AgentTypeDiscovery(Protocol):
    def discover_agent_types(self) -> list[str]:
        ...


def generate_tools_documentation(tools, agent_type_discovery: AgentTypeDiscovery):
    tools_lines = []
    for tool in tools:
        tool_doc = _generate_tool_documentation(tool, agent_type_discovery)
        tools_lines.append(tool_doc)
    return "\n\n".join(tools_lines)


def _generate_tool_documentation(tool, agent_type_discovery: AgentTypeDiscovery):
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
        agent_types = agent_type_discovery.discover_agent_types()
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
