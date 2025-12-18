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

    tools_header = f"""
# Tool Call Format

There is only one valid way to invoke tools!
So it is important that you read the tool call format **carefully**!

{syntax_examples}

Tool calls may appear anywhere in an assistant message, mixed with normal text.
When you call a tool, you'll receive back the result.

# Your Tools

"""
    tools_lines = []
    for tool in tools:
        tool_doc = _generate_tool_documentation(tool, tool_syntax)
        tools_lines.append(tool_doc)
    return tools_header + "\n\n".join(tools_lines) + "\n"


def _generate_syntax_examples(tool_syntax: ToolSyntax) -> str:
    """Generate 2-3 examples showing the tool call syntax."""
    examples = []

    # Example 1: Bodyless tool with required arguments
    example1_tool = _MockTool(
        name="example_tool",
        arguments=ToolArguments(
            header=[
                ToolArgument(name="required_arg", description="", required=True),
                ToolArgument(name="optional_arg", description="", required=False),
            ]
        )
    )
    example1 = tool_syntax._format_example(
        {"required_arg": "arg1", "optional_arg": "arg2"},
        example1_tool
    )
    examples.append(f"Example:\n{example1}")

    # Example 2: Tool with body
    example2_tool = _MockTool(
        name="example_tool_with_body",
        arguments=ToolArguments(
            header=[ToolArgument(name="header_arg", description="", required=True)],
            body=ToolArgument(name="body_content", description="", required=True)
        )
    )
    example2 = tool_syntax._format_example(
        {"header_arg": "header", "body_content": "body"},
        example2_tool
    )
    examples.append(f"Example (tool with body):\n{example2}")

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
