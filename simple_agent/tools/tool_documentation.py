import glob
import os


def generate_tools_documentation(tools):
    tools_lines = []
    for tool in tools:
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
    simple_agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern = os.path.join(simple_agent_dir, '*.agent.md')
    agent_files = glob.glob(pattern)
    agent_types = []
    for filepath in agent_files:
        basename = os.path.basename(filepath)
        agent_type = basename.replace('.agent.md', '')
        agent_types.append(agent_type)
    return sorted(agent_types)
