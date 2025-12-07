from dataclasses import is_dataclass, asdict
from typing import Any, Dict, Iterable

from simple_agent.application.tool_library import Tool, RawToolCall
from simple_agent.application.tool_syntax import ParsedMessage, ToolSyntax


class EmojiBracketToolSyntax(ToolSyntax):
    """Emoji-bracket syntax implementation per v1 spec.

    This implements the 🛠️[tool_name args]...🛠️[/end] syntax as specified in
    doc/emoji_bracket_tool_syntax.spec.md
    """

    def render_documentation(self, tool: Tool) -> str:
        """Generate documentation using 🛠️[tool_name args] bracket syntax."""
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
        else:
            normalized_args = []

        # Generate syntax (always show usage)
        lines.append("")
        required_args = [f"<{arg['name']}>" for arg in normalized_args if arg.get('required', False)]
        optional_args = [f"[{arg['name']}]" for arg in normalized_args if not arg.get('required', False)]
        all_args = required_args + optional_args
        syntax = f"🛠️[{tool.name}"
        if all_args:
            syntax += " " + " ".join(all_args)
        syntax += "]"
        lines.append(f"Usage: {syntax}")

        if hasattr(tool, 'examples') and tool.examples:
            lines.append("")
            lines.append("Examples:")
            example_args = [self._normalize_argument(arg) for arg in tool.arguments]
            for example in tool.examples:
                lines.append(self._format_example(example, example_args, tool.name))

        return "\n".join(lines)

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
        """Format an example in emoji bracket syntax."""
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

        syntax = f"🛠️[{tool_name}"
        if inline_values:
            syntax += " " + " ".join(inline_values)
        syntax += "]"

        if multiline_values:
            multiline_text = "\n".join(multiline_values)
            syntax += "\n" + multiline_text
            syntax += "\n🛠️[/end]"
        else:
            syntax += "\n🛠️[/end]"

        return syntax

    def parse(self, text: str) -> ParsedMessage:
        START_MARKER = "🛠️["
        END_MARKER = "🛠️[/end]"

        tool_calls = []
        message = ""
        first_tool_found = False

        pos = 0
        while pos < len(text):
            # Look for start marker
            start_idx = text.find(START_MARKER, pos)

            if start_idx == -1:
                # No more tool calls found
                if not first_tool_found:
                    message = text
                break

            # Capture message before first tool call
            if not first_tool_found:
                message = text[:start_idx].rstrip()
                first_tool_found = True

            # Find closing bracket for header
            header_start = start_idx + len(START_MARKER)
            header_end = text.find("]", header_start)

            if header_end == -1:
                # Missing closing bracket - treat as plain text and continue
                # If this was the first potential tool, include everything as message
                if not tool_calls:
                    message = text
                    break
                pos = start_idx + len(START_MARKER)
                continue

            # Extract header
            header = text[header_start:header_end]

            # Parse header: first token is tool name, rest is arguments
            header_parts = header.split(None, 1)
            if not header_parts:
                # Empty header - treat as plain text
                pos = header_end + 1
                continue

            tool_name = header_parts[0]
            arguments = header_parts[1] if len(header_parts) > 1 else ""

            # Find end marker
            body_start = header_end + 1
            end_idx = text.find(END_MARKER, body_start)

            if end_idx == -1:
                # Missing end marker - best effort: treat rest as body
                body = text[body_start:].rstrip()
                tool_calls.append(RawToolCall(name=tool_name, arguments=arguments, body=body))
                break

            # Extract body (skip leading newline if present)
            body_text = text[body_start:end_idx]
            if body_text.startswith('\n'):
                body_text = body_text[1:]
            elif body_text.startswith('\r\n'):
                body_text = body_text[2:]
            body = body_text.rstrip('\n\r')

            tool_calls.append(RawToolCall(name=tool_name, arguments=arguments, body=body))

            # Continue after end marker
            pos = end_idx + len(END_MARKER)

        return ParsedMessage(message=message, tool_calls=tool_calls)
