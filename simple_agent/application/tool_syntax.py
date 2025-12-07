"""Tool syntax abstraction for formatting and parsing tool calls."""

import re
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Protocol

from simple_agent.application.tool_library import Tool
from simple_agent.application.tool_message_parser import ParsedMessage, RawToolCall


class ToolSyntax(Protocol):
    """Abstraction for tool call syntax formatting and parsing."""

    def render_documentation(self, tool: Tool) -> str:
        """
        Generate complete documentation for a tool.

        Includes:
        - Tool name and description
        - Arguments list with types/descriptions
        - Usage syntax line
        - Formatted examples

        Args:
            tool: Tool to document (pure data)

        Returns:
            Formatted documentation string
        """
        ...

    def parse(self, text: str) -> ParsedMessage:
        """
        Extract tool calls from text.

        Args:
            text: Raw text from LLM response

        Returns:
            ParsedMessage(message, tool_calls)
            - message: Text before first tool call
            - tool_calls: List of RawToolCall instances
        """
        ...


class EmojiToolSyntax:
    """Current 🛠️-based syntax implementation."""

    def render_documentation(self, tool: Tool) -> str:
        """Generate documentation using 🛠️ emoji syntax."""
        lines = [f"Tool: {tool.name}"]

        if hasattr(tool, 'description') and tool.description:
            lines.append(f"Description: {tool.description}")

        if hasattr(tool, 'arguments') and tool.arguments:
            lines.append("")
            lines.append("Arguments:")
            normalized_args = [self._normalize_argument(arg) for arg in tool.arguments]
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
            example_args = [self._normalize_argument(arg) for arg in tool.arguments]
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

                all_arg_lines = []
                if same_line_args:
                    all_arg_lines.append(same_line_args)

                i += 1
                while i < len(lines) and not re.match(r'^🛠️ ', lines[i]) and not re.match(end_marker, lines[i]):
                    all_arg_lines.append(lines[i])
                    i += 1

                if i < len(lines) and re.match(end_marker, lines[i]):
                    i += 1

                arguments = ''.join(all_arg_lines).rstrip()
                tool_calls.append(RawToolCall(command, arguments))
            else:
                i += 1

        if tool_calls:
            return ParsedMessage(message=message, tool_calls=tool_calls)
        return ParsedMessage(message=text, tool_calls=[])

    def _normalize_argument(self, arg: Any) -> Dict[str, Any]:
        """Normalize argument to dict format."""
        if is_dataclass(arg):
            normalized = asdict(arg)
        else:
            normalized = dict(arg)

        normalized.setdefault("type", "string")
        normalized.setdefault("required", False)
        normalized.setdefault("description", "")
        normalized.setdefault("multiline", False)
        return normalized

    def _format_example(self, example: Any, arguments: Iterable[Dict[str, Any]], tool_name: str) -> str:
        """Format an example tool call using 🛠️ syntax."""
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
