import shlex
from dataclasses import replace
from typing import Any

from simple_agent.application.tool_library import (
    RawToolCall,
    Tool,
    ToolArgument,
    ToolArguments,
    is_true,
)
from simple_agent.application.tool_syntax import RawAssistantTurn, ToolSyntax


class EmojiBracketToolSyntax(ToolSyntax):
    """Emoji-bracket syntax implementation per v1 spec.

    This implements the 🛠️[tool_name args]...🛠️[/end] syntax as specified in
    docs/emoji_bracket_tool_syntax.spec.md
    """

    def render_documentation(self, tool: Tool) -> str:
        lines = [f"Tool: {tool.name}"]

        if hasattr(tool, "description") and tool.description:
            lines.append(f"Description: {tool.description}")

        lines.append("")
        syntax = self.build_syntax(tool)
        lines.append(f"### Usage:\n{syntax}")

        if tool.arguments:
            lines.append("")
            lines.append("### Arguments:")
            for arg in tool.arguments.all:
                lines.append(self._format_arg_doc(arg))

        if hasattr(tool, "examples") and tool.examples:
            lines.append("")
            lines.append("### Examples:\n")
            for i, example in enumerate(tool.examples):
                if i > 0:
                    lines.append("")  # Add blank line between examples
                lines.append(self._format_example(example, tool))

        return "\n".join(lines)

    def build_syntax(self, tool):
        syntax_parts = []
        if tool.arguments:
            for arg in tool.arguments.header:
                syntax_parts.append(
                    "{" + f"{arg.name}" + "}" if arg.required else f"[{arg.name}]"
                )
        syntax = f"🛠️[{tool.name}"
        if syntax_parts:
            syntax += " " + " ".join(syntax_parts)
        if tool.arguments.body:
            syntax += "]"
            syntax += "\n{content}\n🛠️[/end]"
        else:
            syntax += " /]"
        return syntax

    def _format_arg_doc(self, arg: ToolArgument) -> str:
        """Format a single argument for documentation."""
        required_str = " (required)" if arg.required else " (optional)"
        type_str = f" - {arg.name}: {arg.type}{required_str}"
        if arg.description:
            type_str += f" - {arg.description}"
        return type_str

    def _format_example(self, example: Any, tool: Tool) -> str:
        """Format an example in emoji bracket syntax.

        Supports optional fields in example dict:
        - 'reasoning': Context/explanation before the tool call
        - 'result': Result output to display after the tool call
        - All other fields are treated as arguments
        """
        if isinstance(example, str):
            return example

        if not isinstance(example, dict):
            return str(example)

        # Extract optional fields
        reasoning = example.get("reasoning")
        result = example.get("result")
        # Create a copy without special fields for formatting
        example_without_special = {
            k: v for k, v in example.items() if k not in ("reasoning", "result")
        }

        # Collect inline argument values (header args)
        inline_values = []
        for arg in tool.arguments:
            value = example_without_special.get(arg.name, "")
            if arg.is_flag:
                if is_true(value):
                    inline_values.append(arg.name)
            elif value:
                inline_values.append(str(value))

        # Collect body value
        body_value = ""
        if tool.arguments.body:
            value = example_without_special.get(tool.arguments.body.name, "")
            if value:
                body_value = str(value)

        syntax = f"🛠️[{tool.name}"
        if inline_values:
            syntax += " " + " ".join(inline_values)

        if body_value:
            syntax += "]"
            syntax += "\n" + body_value
            syntax += "\n🛠️[/end]"
        else:
            # Self-closing syntax for bodyless tools
            syntax += " /]"

        # Build complete conversation pattern
        output_lines = []

        # Add reasoning if present
        if reasoning:
            output_lines.append(reasoning)

        # Add tool call
        output_lines.append(syntax)

        # Append result if present
        if result:
            result_header = (
                f"\nThen you will receive a result:\nResult of 🛠️ {tool.name}"
            )
            if inline_values:
                result_header += " " + " ".join(inline_values)
            output_lines.append(result_header)
            output_lines.append(result)

        output_lines.append("\n-")

        return "\n".join(output_lines)

    def bind(self, raw_call: RawToolCall, tool: Tool) -> RawToolCall:
        """
        Complete a call so it carries both its named arguments and its text.

        A call made under the text protocol gets its positional header bound
        to the tool's declared names: a single header argument takes the whole
        text as it was written; a longer header is split shell-style so a
        quoted value stays one value, and any tokens beyond the header flow
        into its last argument. Boolean arguments are flags: they bind by name
        wherever they appear. A call made natively, carrying only the named
        arguments, gets its header text and body rendered from them.
        """
        if raw_call.named_arguments:
            return self._render_text(raw_call, tool)
        try:
            named = self._bind_header(raw_call.arguments, tool.arguments)
        except ValueError:
            return raw_call
        if tool.arguments.body and raw_call.body:
            named[tool.arguments.body.name] = raw_call.body
        return replace(raw_call, named_arguments=named)

    def _render_text(self, raw_call: RawToolCall, tool: Tool) -> RawToolCall:
        if raw_call.arguments or raw_call.body:
            return raw_call
        named = raw_call.named_arguments
        body_argument = tool.arguments.body
        body = str(named.get(body_argument.name, "")) if body_argument else ""
        return replace(raw_call, arguments=self.render_header(named, tool), body=body)

    def _bind_header(self, text: str, arguments: ToolArguments) -> dict[str, Any]:
        if not text or not arguments.header:
            return {}
        if arguments.single_positional:
            return {arguments.single_positional.name: text}
        values = shlex.split(text)
        named: dict[str, Any] = {
            flag.name: True for flag in arguments.flags if flag.name in values
        }
        values = [value for value in values if value not in named]
        positional = arguments.positional
        last = len(positional) - 1
        if len(values) > len(positional):
            values[last:] = [" ".join(values[last:])]
        named.update(zip((arg.name for arg in positional), values, strict=False))
        return named

    def render_header(self, named: dict[str, Any], tool: Tool) -> str:
        """
        Render named arguments as the positional header text, the inverse of
        bind: a single header argument is written as is, other values are
        shell-quoted when needed, and a true flag appears by name.
        """
        arguments = tool.arguments
        if arguments.single_positional:
            return str(named.get(arguments.single_positional.name, ""))
        parts = [
            shlex.quote(str(named[arg.name]))
            for arg in arguments.positional
            if arg.name in named
        ]
        parts.extend(
            flag.name for flag in arguments.flags if is_true(named.get(flag.name))
        )
        return " ".join(parts)

    def contains_call(self, text: str) -> bool:
        return any(marker in text for marker in ("🛠️[", "🛠["))

    def render_call(self, raw_call: RawToolCall) -> str:
        header = f"{raw_call.name} {raw_call.arguments}".strip()
        if raw_call.body:
            return f"🛠️[{header}]\n{raw_call.body}\n🛠️[/end]"
        return f"🛠️[{header} /]"

    def parse(self, text: str) -> RawAssistantTurn:
        # Markers can appear with or without variation selector (U+FE0F)
        # 🛠️ is U+1F6E0 U+FE0F
        # 🛠 is U+1F6E0
        START_MARKERS = ["🛠️[", "🛠["]
        END_MARKERS = ["🛠️[/end]", "🛠[/end]"]
        SELF_CLOSING_SUFFIX = " /]"

        def find_any(markers, start_pos) -> tuple[int, str]:
            earliest = -1
            found_marker = ""
            for marker in markers:
                idx = text.find(marker, start_pos)
                if idx != -1 and (earliest == -1 or idx < earliest):
                    earliest = idx
                    found_marker = marker
            return earliest, found_marker

        tool_calls = []
        message = ""
        first_tool_found = False

        pos = 0
        while pos < len(text):
            # Look for start marker
            start_idx, current_start_marker = find_any(START_MARKERS, pos)

            if start_idx == -1:
                # No more tool calls found
                if not first_tool_found:
                    message = text
                break

            # Capture message before first tool call
            if not first_tool_found:
                message = text[:start_idx].rstrip()
                first_tool_found = True

            # Find closing bracket for header - check for self-closing first
            header_start = start_idx + len(current_start_marker)
            self_closing_idx = text.find(SELF_CLOSING_SUFFIX, header_start)
            regular_close_idx = text.find("]", header_start)

            # Determine if this is self-closing
            is_self_closing = False
            header_end = -1

            if self_closing_idx != -1:
                # Check if this self-closing comes before a regular close
                if (
                    regular_close_idx == -1
                    or self_closing_idx + len(SELF_CLOSING_SUFFIX) - 1
                    == regular_close_idx
                ):
                    is_self_closing = True
                    header_end = self_closing_idx

            if not is_self_closing:
                if regular_close_idx == -1:
                    # Missing closing bracket - treat as plain text and continue
                    if not tool_calls:
                        message = text
                        break
                    pos = start_idx + len(current_start_marker)
                    continue
                header_end = regular_close_idx

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

            if is_self_closing:
                # Self-closing tool call - no body
                tool_calls.append(
                    RawToolCall(name=tool_name, arguments=arguments, body="")
                )
                pos = header_end + len(SELF_CLOSING_SUFFIX)
            else:
                # Tool call with body - must find matching end marker
                after_header = header_end + 1
                search_pos = after_header
                depth = 1
                end_idx = -1
                current_end_marker = ""
                last_end_idx = -1
                last_end_marker = ""

                while True:
                    next_start_idx, next_start_marker = find_any(
                        START_MARKERS, search_pos
                    )
                    next_end_idx, next_end_marker = find_any(END_MARKERS, search_pos)

                    if next_end_idx == -1:
                        if last_end_idx != -1:
                            end_idx = last_end_idx
                            current_end_marker = last_end_marker
                        else:
                            # Missing end marker - best effort: treat rest as body
                            body = text[after_header:].rstrip()
                            if body.startswith("\n"):
                                body = body[1:]
                            elif body.startswith("\r\n"):
                                body = body[2:]
                            tool_calls.append(
                                RawToolCall(
                                    name=tool_name, arguments=arguments, body=body
                                )
                            )
                            pos = len(text)
                        break

                    if next_start_idx != -1 and next_start_idx < next_end_idx:
                        # Nested start marker - track depth but allow fallback if unclosed
                        depth += 1
                        search_pos = next_start_idx + len(next_start_marker)
                        continue

                    depth -= 1
                    last_end_idx = next_end_idx
                    last_end_marker = next_end_marker
                    if depth == 0:
                        end_idx = next_end_idx
                        current_end_marker = next_end_marker
                        break

                    search_pos = next_end_idx + len(next_end_marker)

                if end_idx != -1:
                    # Extract body (skip leading newline if present)
                    body_text = text[after_header:end_idx]
                    if body_text.startswith("\n"):
                        body_text = body_text[1:]
                    elif body_text.startswith("\r\n"):
                        body_text = body_text[2:]
                    body = body_text.rstrip("\n\r")

                    tool_calls.append(
                        RawToolCall(name=tool_name, arguments=arguments, body=body)
                    )

                    # Continue after end marker
                    pos = end_idx + len(current_end_marker)

        return RawAssistantTurn(message=message, tool_calls=tool_calls)
