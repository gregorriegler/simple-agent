import re
from dataclasses import is_dataclass, asdict
from typing import Any, Dict, Iterable

from simple_agent.application.tool_library import Tool
from simple_agent.application.tool_syntax import ParsedMessage, RawToolCall, ToolSyntax


class EmojiToolSyntax (ToolSyntax):
    """Current 🛠️-based syntax implementation."""

    def render_documentation(self, tool: Tool) -> str:
        """Generate documentation using 🛠️ emoji syntax."""
        lines = [f"Tool: {tool.name}"]

        if hasattr(tool, 'description') and tool.description:
            lines.append(f"Description: {tool.description}")

        # Combine arguments and body for documentation
        all_arguments = []
        body_arg_name = None
        if hasattr(tool, 'arguments') and tool.arguments:
            all_arguments.extend(tool.arguments)
        if hasattr(tool, 'body') and tool.body:
            all_arguments.append(tool.body)
            body_arg_name = tool.body.name

        if all_arguments:
            lines.append("")
            lines.append("Arguments:")
            normalized_args = [self._normalize_argument(arg, is_body=(arg.name == body_arg_name)) for arg in all_arguments]
            for arg in normalized_args:
                required_str = " (required)" if arg.get('required', False) else " (optional)"
                type_str = f" - {arg['name']}: {arg.get('type', 'string')}{required_str}"
                if 'description' in arg:
                    type_str += f" - {arg['description']}"
                lines.append(type_str)

            # Generate syntax
            lines.append("")
            required_args = [f"<{arg['name']}>" for arg in normalized_args if arg.get('required', False)]
            optional_args = [f"[{arg['name']}]" for arg in normalized_args if not arg.get('required', False)]
            all_args = required_args + optional_args
            syntax = f"🛠️ {tool.name}"
            if all_args:
                syntax += " " + " ".join(all_args)
            lines.append(f"Usage: {syntax}")

        if hasattr(tool, 'examples') and tool.examples:
            lines.append("")
            lines.append("Examples:")
            example_args = [self._normalize_argument(arg, is_body=(arg.name == body_arg_name)) for arg in all_arguments]
            for example in tool.examples:
                lines.append(self._format_example(example, example_args, tool.name))

        return "\n".join(lines)

    def parse(self, text: str) -> ParsedMessage:
        """Parse text to extract 🛠️-based tool calls."""
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

    def _normalize_argument(self, arg: Any, is_body: bool = False) -> Dict[str, Any]:
        """Normalize argument to dict format."""
        if is_dataclass(arg):
            normalized = asdict(arg)
        else:
            normalized = dict(arg)

        normalized.setdefault("type", "string")
        normalized.setdefault("required", False)
        normalized.setdefault("description", "")
        # Mark body arguments as multiline for formatting purposes
        normalized["multiline"] = is_body
        return normalized

    def _format_example(self, example: Any, arguments: Iterable[Dict[str, Any]], tool_name: str) -> str:
        if isinstance(example, str):
            return example

        if not isinstance(example, dict):
            return str(example)

        inline_values = []
        multiline_values = []

        for arg in arguments:
            value = example.get(arg["name"], "")
            if value is None:
                value = ""

            if arg.get("multiline"):
                if value != "":
                    multiline_values.append(str(value))
            else:
                if value != "":
                    inline_values.append(str(value))

        syntax = f"🛠️ {tool_name}"
        if inline_values:
            syntax += " " + " ".join(inline_values)

        if multiline_values:
            multiline_text = "\n".join(multiline_values)
            syntax += "\n" + multiline_text
            if multiline_text.endswith("\n"):
                syntax += "🛠️🔚"
            elif "\n" in multiline_text:
                syntax += "\n🛠️🔚"
            else:
                syntax += "🛠️🔚"

        return syntax
