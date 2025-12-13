from typing import Any

from simple_agent.application.tool_library import Tool, ToolArgument, RawToolCall
from simple_agent.application.tool_syntax import ParsedMessage, ToolSyntax


class EmojiBracketToolSyntax(ToolSyntax):
    """Emoji-bracket syntax implementation per v1 spec.

    This implements the 🛠️[tool_name args]...🛠️[/end] syntax as specified in
    doc/emoji_bracket_tool_syntax.spec.md
    """

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
        if tool.arguments:
            for arg in tool.arguments.header:
                syntax_parts.append(f"<{arg.name}>" if arg.required else f"[{arg.name}]")
        syntax = f"🛠️[{tool.name}"
        if syntax_parts:
            syntax += " " + " ".join(syntax_parts)
        syntax += "]"
        if tool.arguments.body:
            syntax += "\n<content>\n🛠️[/end]"

        lines.append(f"Usage:\n{syntax}")

        if hasattr(tool, 'examples') and tool.examples:
            lines.append("")
            lines.append("Examples:")
            for example in tool.examples:
                lines.append(self._format_example(example, tool))

        return "\n".join(lines)

    def _format_arg_doc(self, arg: ToolArgument) -> str:
        """Format a single argument for documentation."""
        required_str = " (required)" if arg.required else " (optional)"
        type_str = f" - {arg.name}: {arg.type}{required_str}"
        if arg.description:
            type_str += f" - {arg.description}"
        return type_str

    def _format_example(self, example: Any, tool: Tool) -> str:
        """Format an example in emoji bracket syntax."""
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

        syntax = f"🛠️[{tool.name}"
        if inline_values:
            syntax += " " + " ".join(inline_values)
        syntax += "]"

        if body_value:
            syntax += "\n" + body_value
            syntax += "\n🛠️[/end]"
        # No [/end] needed for bodyless tools

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

            # Determine if this is a bodyless tool call or has a body
            # Look for the next START_MARKER and END_MARKER after the header
            after_header = header_end + 1
            next_start_idx = text.find(START_MARKER, after_header)
            end_idx = text.find(END_MARKER, after_header)

            # Check if this is a bodyless call:
            # - No end marker exists, or
            # - Next start marker comes before end marker (with only whitespace between)
            # - End of string comes right after header (with only whitespace)
            text_after_header = text[after_header:]

            is_bodyless = False
            if end_idx == -1:
                # No end marker - check if next tool or end of string
                if next_start_idx == -1:
                    # No more tools, no end marker - bodyless if only whitespace remains
                    is_bodyless = text_after_header.strip() == ""
                else:
                    # Next tool exists - bodyless if only whitespace before it
                    between = text[after_header:next_start_idx]
                    is_bodyless = between.strip() == ""
            elif next_start_idx != -1 and next_start_idx < end_idx:
                # Next tool comes before end marker - bodyless if only whitespace between
                between = text[after_header:next_start_idx]
                is_bodyless = between.strip() == ""

            if is_bodyless:
                # Bodyless tool call
                tool_calls.append(RawToolCall(name=tool_name, arguments=arguments, body=""))
                if next_start_idx != -1:
                    pos = next_start_idx
                else:
                    break
            else:
                # Tool call with body - find end marker
                if end_idx == -1:
                    # Missing end marker - best effort: treat rest as body
                    body = text[after_header:].rstrip()
                    if body.startswith('\n'):
                        body = body[1:]
                    elif body.startswith('\r\n'):
                        body = body[2:]
                    tool_calls.append(RawToolCall(name=tool_name, arguments=arguments, body=body))
                    break

                # Extract body (skip leading newline if present)
                body_text = text[after_header:end_idx]
                if body_text.startswith('\n'):
                    body_text = body_text[1:]
                elif body_text.startswith('\r\n'):
                    body_text = body_text[2:]
                body = body_text.rstrip('\n\r')

                tool_calls.append(RawToolCall(name=tool_name, arguments=arguments, body=body))

                # Continue after end marker
                pos = end_idx + len(END_MARKER)

        return ParsedMessage(message=message, tool_calls=tool_calls)
