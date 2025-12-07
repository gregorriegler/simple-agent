from simple_agent.application.tool_syntax import ToolSyntax


def generate_tools_documentation(tools, tool_syntax: ToolSyntax) -> str:
    tools_header = """# Tools

To use a tool, answer in the described syntax.
One tool execution per answer.
The tool should always be the last thing in your answer."""
    tools_lines = []
    for tool in tools:
        tool_doc = _generate_tool_documentation(tool, tool_syntax)
        tools_lines.append(tool_doc)
    return tools_header + "\n\n".join(tools_lines)


def _generate_tool_documentation(tool, syntax):
    usage_info = syntax.render_documentation(tool)

    # Substitute template variables
    template_vars = tool.get_template_variables()
    for key, value in template_vars.items():
        usage_info = usage_info.replace(f'{{{{{key}}}}}', value)

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
