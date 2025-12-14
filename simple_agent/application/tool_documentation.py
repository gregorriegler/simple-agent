from simple_agent.application.tool_syntax import ToolSyntax
from simple_agent.application.tool_library import Tool, ToolArgument, ToolArguments


class _MockTool:
    """Mock tool for generating syntax examples."""
    def __init__(self, name: str, arguments: ToolArguments):
        self.name = name
        self.arguments = arguments
        self.description = ""
        self.examples = []

    def get_template_variables(self):
        return {}


def generate_tools_documentation(tools, tool_syntax: ToolSyntax) -> str:
    # Generate syntax examples
    syntax_examples = _generate_syntax_examples(tool_syntax)

    tools_header = f"""# Tools

To use a tool, answer in the described syntax.
Tool calls should always be the last things in your answer.

{syntax_examples}

"""
    tools_lines = []
    for tool in tools:
        tool_doc = _generate_tool_documentation(tool, tool_syntax)
        tools_lines.append(tool_doc)
    return tools_header + "\n\n".join(tools_lines)


def _generate_syntax_examples(tool_syntax: ToolSyntax) -> str:
    """Generate 2-3 examples showing the tool call syntax."""
    examples = []

    # Example 1: Bodyless tool with required arguments
    example1_tool = _MockTool(
        name="MOCK_TOOL_NAME",
        arguments=ToolArguments(
            header=[
                ToolArgument(name="required_arg", description="", required=True),
                ToolArgument(name="optional_arg", description="", required=False),
            ]
        )
    )
    example1 = tool_syntax._format_example(
        {"required_arg": "REQUIRED_VALUE", "optional_arg": "OPTIONAL_VALUE"},
        example1_tool
    )
    examples.append(f"Syntax Example (bodyless tool):\n{example1}")

    # Example 2: Tool with body
    example2_tool = _MockTool(
        name="MOCK_TOOL_WITH_BODY",
        arguments=ToolArguments(
            header=[ToolArgument(name="header_arg", description="", required=True)],
            body=ToolArgument(name="body_content", description="", required=True)
        )
    )
    example2 = tool_syntax._format_example(
        {"header_arg": "HEADER_VALUE", "body_content": "EXAMPLE BODY CONTENT HERE"},
        example2_tool
    )
    examples.append(f"Syntax Example (tool with body):\n{example2}")

    return "\n\n".join(examples)


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

    doc_lines = [f"## {tool_name} tool"]
    if description:
        doc_lines.append(f"{description}")

    remaining_lines = usage_info.split('\n')[2:]

    if remaining_lines:
        doc_lines.extend(remaining_lines)

    return "\n".join(doc_lines)
