from typing import List

from simple_agent.application.tool_syntax import EmojiToolSyntax

CURRENT_SYNTAX = EmojiToolSyntax()


def generate_tools_documentation(tools, agent_types: List[str]) -> str:
    tools_header = """# Tools

To use a tool, answer in the described syntax.
One tool execution per answer.
The tool should always be the last thing in your answer."""
    tools_lines = []
    context = {'agent_types': agent_types}
    for tool in tools:
        tool_doc = _generate_tool_documentation(tool, context, CURRENT_SYNTAX)
        tools_lines.append(tool_doc)
    return tools_header + "\n\n".join(tools_lines)


def _generate_tool_documentation(tool, context: dict, syntax=None):
    if syntax is not None:
        try:
            usage_info = syntax.render_documentation(tool)
        except (AttributeError, TypeError):
            usage_info = tool.get_usage_info(syntax)
    else:
        usage_info = tool.get_usage_info(CURRENT_SYNTAX)
    usage_info = tool.finalize_documentation(usage_info, context)

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

    doc_lines = [f"## {tool_name}"]
    if description:
        doc_lines.append(f"{description}")

    remaining_lines = usage_info.split('\n')[2:]

    if remaining_lines:
        doc_lines.extend(remaining_lines)

    return "\n".join(doc_lines)
