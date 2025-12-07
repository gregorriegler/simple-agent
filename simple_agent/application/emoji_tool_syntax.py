import re
from typing import Any

from simple_agent.application.tool_library import Tool, ToolArgument
from simple_agent.application.tool_syntax import ParsedMessage, RawToolCall, ToolSyntax


class EmojiToolSyntax (ToolSyntax):

    def render_documentation(self, tool: Tool) -> str:
        lines = [f"Tool: {tool.name}"]

        if hasattr(tool, 'description') and tool.description:
            lines.append(f"Description: {tool.description}")

        if tool.arguments:
            lines.append("")
            lines.append("Arguments:")

            for arg in tool.arguments.all:
                lines.append(self._format_arg_doc(arg))

            lines.append("")
            syntax_parts = []
            for arg in tool.arguments.all:
                syntax_parts.append(f"<{arg.name}>" if arg.required else f"[{arg.name}]")
            syntax = f"🛠️ {tool.name}"
            if syntax_parts:
                syntax += " " + " ".join(syntax_parts)
            lines.append(f"Usage: {syntax}")

        if hasattr(tool, 'examples') and tool.examples:
            lines.append("")
            lines.append("Examples:")
            for example in tool.examples:
                lines.append(self._format_example(example, tool))

        return "\n".join(lines)

    def _format_arg_doc(self, arg: ToolArgument) -> str:
        required_str = " (required)" if arg.required else " (optional)"
        type_str = f" - {arg.name}: {arg.type}{required_str}"
        if arg.description:
            type_str += f" - {arg.description}"
        return type_str

    def parse(self, text: str) -> ParsedMessage:
        pattern = r'^🛠️ ([\w-]+)(?:\s+(.*))?'
        end_marker = r'^🛠️🔚'
        lines = text.splitlines(keepends=True)
        tool_calls = []
        message = ""
        first_tool_index = None

        i = 0
        while i < len(lines):
            match = re.match(pattern, lines[i], re.DOTALL)
            if match:
                if first_tool_index is None:
                    first_tool_index = i
                    message = ''.join(lines[:i]).rstrip()

                command, same_line_args = match.groups()

                # Collect first line arguments (inline)
                inline_args = same_line_args.rstrip('\n\r') if same_line_args else ""

                # Collect body content (multiline content after the first line)
                body_lines = []
                i += 1
                while i < len(lines) and not re.match(r'^🛠️ ', lines[i]) and not re.match(end_marker, lines[i]):
                    body_lines.append(lines[i])
                    i += 1

                if i < len(lines) and re.match(end_marker, lines[i]):
                    i += 1

                body = ''.join(body_lines).rstrip() if body_lines else ""
                arguments = inline_args

                tool_calls.append(RawToolCall(name=command, arguments=arguments, body=body))
            else:
                i += 1

        if tool_calls:
            return ParsedMessage(message=message, tool_calls=tool_calls)
        return ParsedMessage(message=text, tool_calls=[])

    def _format_example(self, example: Any, tool: Tool) -> str:
        if isinstance(example, str):
            return example

        if not isinstance(example, dict):
            return str(example)

        # Collect inline argument values (header args)
        inline_values = []
        for arg in tool.arguments:
            value = example.get(arg.name, "")
            if value:
                inline_values.append(str(value))

        # Collect body value
        body_value = ""
        if tool.arguments.body:
            value = example.get(tool.arguments.body.name, "")
            if value:
                body_value = str(value)

        syntax = f"🛠️ {tool.name}"
        if inline_values:
            syntax += " " + " ".join(inline_values)

        if body_value:
            syntax += "\n" + body_value
            if body_value.endswith("\n"):
                syntax += "🛠️🔚"
            elif "\n" in body_value:
                syntax += "\n🛠️🔚"
            else:
                syntax += "🛠️🔚"

        return syntax
