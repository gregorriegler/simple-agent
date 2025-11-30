# Extract Tool Message Parser to Application Layer

## Goal

Move pure parsing logic from the tools layer to the application layer, enabling unit testing without infrastructure dependencies.

## Problem Statement

The `parse_message_and_tools()` method in `AllTools` is pure string parsing logic (regex matching, line iteration) with no I/O. However, it currently lives in `simple_agent/tools/all_tools.py`, which means:

1. **Testing requires infrastructure setup**: To test parsing, you must instantiate `AllTools`, which requires a `ToolContext` and `SubagentSpawner`
2. **Violates ports & adapters**: Pure business logic is mixed with tool registration/execution infrastructure
3. **High coupling**: The parser depends on `self.tool_dict` to validate tool names, coupling parsing to tool instantiation

## Current Location

`simple_agent/tools/all_tools.py:55-95`

```python
def parse_message_and_tools(self, text) -> MessageAndParsedTools:
    pattern = r'^🛠️ ([\w-]+)(?:\s+(.*))?'
    end_marker = r'^🛠️🔚'
    lines = text.splitlines(keepends=True)
    parsed_tools = []
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
            tool = self.tool_dict.get(command)
            if not tool:
                return MessageAndParsedTools(message=text, tools=[])

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
            parsed_tools.append(ParsedTool(command, arguments, tool))
        else:
            i += 1

    if parsed_tools:
        return MessageAndParsedTools(message=message, tools=parsed_tools)
    return MessageAndParsedTools(message=text, tools=[])
```

## Refactoring Steps

### Step 1: Create new application module

Create `simple_agent/application/tool_message_parser.py` with a pure function:

```python
import re
from dataclasses import dataclass
from .tool_library import MessageAndParsedTools, ParsedTool, Tool


@dataclass
class RawToolCall:
    """Parsed tool call before tool instance resolution."""
    name: str
    arguments: str


@dataclass
class ParsedMessage:
    """Result of parsing LLM response for tool calls."""
    message: str
    tool_calls: list[RawToolCall]


def parse_tool_calls(text: str) -> ParsedMessage:
    """
    Parse LLM response text for tool calls.

    Returns the message portion and a list of raw tool calls.
    Does NOT validate tool names - that's the caller's responsibility.
    """
    # Move parsing logic here, but return RawToolCall instead of ParsedTool
    ...
```

### Step 2: Decide on tool validation strategy

The current code returns early with no tools if an unknown tool name is found. Decide:

**Option A**: Parser returns raw calls, `AllTools` validates and resolves to `ParsedTool`
- Cleaner separation
- Parser is purely syntactic

**Option B**: Parser accepts a `known_tools: set[str]` parameter for validation
- Keeps validation in parser
- Slightly more coupled

Recommend **Option A** for cleaner separation.

### Step 3: Update AllTools to use the parser

```python
# simple_agent/tools/all_tools.py

from simple_agent.application.tool_message_parser import parse_tool_calls

class AllTools(ToolLibrary):

    def parse_message_and_tools(self, text) -> MessageAndParsedTools:
        parsed = parse_tool_calls(text)

        tools = []
        for raw_call in parsed.tool_calls:
            tool_instance = self.tool_dict.get(raw_call.name)
            if not tool_instance:
                # Unknown tool - return message as-is with no tools
                return MessageAndParsedTools(message=text, tools=[])
            tools.append(ParsedTool(raw_call.name, raw_call.arguments, tool_instance))

        return MessageAndParsedTools(message=parsed.message, tools=tools)
```

### Step 4: Add unit tests for parser

Create `tests/application/test_tool_message_parser.py`:

```python
from simple_agent.application.tool_message_parser import parse_tool_calls

def test_parse_simple_tool_call():
    text = "Hello\n🛠️ bash echo hello"
    result = parse_tool_calls(text)
    assert result.message == "Hello"
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "bash"
    assert result.tool_calls[0].arguments == "echo hello"

def test_parse_multiline_arguments():
    text = "Message\n🛠️ create_file path.txt\nline1\nline2\n🛠️🔚"
    result = parse_tool_calls(text)
    assert result.tool_calls[0].arguments == "path.txt\nline1\nline2"

def test_parse_no_tools():
    text = "Just a message with no tools"
    result = parse_tool_calls(text)
    assert result.message == "Just a message with no tools"
    assert result.tool_calls == []

def test_parse_multiple_tools():
    text = "Start\n🛠️ ls\n🛠️ bash pwd"
    result = parse_tool_calls(text)
    assert len(result.tool_calls) == 2
```

### Step 5: Update existing tests

Ensure any existing tests for `AllTools.parse_message_and_tools()` still pass. They now test the integration of parser + tool resolution.

## Expected Outcome

- `parse_tool_calls()` is a pure function in the application layer
- Unit tests for parsing don't require any tool infrastructure
- `AllTools` becomes thinner - delegates parsing, focuses on tool registry and execution
- Parsing edge cases can be tested exhaustively without setup overhead

## Files Changed

- `simple_agent/application/tool_message_parser.py` (new)
- `simple_agent/tools/all_tools.py` (modified)
- `tests/application/test_tool_message_parser.py` (new)
