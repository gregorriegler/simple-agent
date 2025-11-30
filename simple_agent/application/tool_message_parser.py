import re
from dataclasses import dataclass


@dataclass
class RawToolCall:
    name: str
    arguments: str


@dataclass
class ParsedMessage:
    message: str
    tool_calls: list[RawToolCall]


def parse_tool_calls(text: str) -> ParsedMessage:
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
