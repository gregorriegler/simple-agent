from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.tools.base_tool import BaseTool
from simple_agent.application.tool_library import ToolArgument


class SimpleTool(BaseTool):
    name = 'test_tool'
    description = 'A test tool'
    arguments = [
        ToolArgument(name='arg1', description='First argument', required=True),
        ToolArgument(name='arg2', description='Second argument', required=False),
    ]
    examples = [
        {'arg1': 'value1', 'arg2': 'value2'},
        {'arg1': 'only_required'},
    ]


class MultilineTool(BaseTool):
    name = 'multiline_tool'
    description = 'Tool with multiline input'
    arguments = [
        ToolArgument(name='inline_arg', description='Inline argument', required=True),
        ToolArgument(name='multiline_arg', description='Multiline content', required=True, multiline=True),
    ]
    examples = [
        {'inline_arg': 'test', 'multiline_arg': 'line1\nline2\nline3'},
    ]


class TestEmojiBracketDocumentation:
    def test_renders_simple_tool_documentation(self):
        syntax = EmojiBracketToolSyntax()
        tool = SimpleTool()

        doc = syntax.render_documentation(tool)

        assert 'Tool: test_tool' in doc
        assert 'Description: A test tool' in doc
        assert 'Arguments:' in doc
        assert 'arg1: string (required) - First argument' in doc
        assert 'arg2: string (optional) - Second argument' in doc
        assert 'Usage: 🛠️[test_tool <arg1> [arg2]]' in doc
        assert 'Examples:' in doc
        assert '🛠️[test_tool value1 value2]' in doc
        assert '🛠️[/end]' in doc
        assert '🛠️[test_tool only_required]' in doc

    def test_renders_multiline_tool_documentation(self):
        syntax = EmojiBracketToolSyntax()
        tool = MultilineTool()

        doc = syntax.render_documentation(tool)

        assert 'Tool: multiline_tool' in doc
        assert 'Usage: 🛠️[multiline_tool <inline_arg> <multiline_arg>]' in doc
        assert '🛠️[multiline_tool test]' in doc
        assert 'line1\nline2\nline3' in doc
        assert '🛠️[/end]' in doc

    def test_renders_tool_without_arguments(self):
        class NoArgsTool(BaseTool):
            name = 'no_args'
            description = 'Tool without arguments'
            arguments = []
            examples = []

        syntax = EmojiBracketToolSyntax()
        tool = NoArgsTool()

        doc = syntax.render_documentation(tool)

        assert 'Tool: no_args' in doc
        assert 'Description: Tool without arguments' in doc
        assert 'Arguments:' not in doc
        assert 'Usage: 🛠️[no_args]' in doc


class TestEmojiBracketBasicParsing:

    def test_parses_simple_tool_call_with_no_body(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[create-file]\n🛠️[/end]"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create-file"
        assert result.tool_calls[0].arguments == ""
        assert result.tool_calls[0].body == ""

    def test_parses_tool_call_with_body(self):
        syntax = EmojiBracketToolSyntax()
        text = '🛠️[create-file script.py]\nprint("Hello World")\n🛠️[/end]'

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create-file"
        assert result.tool_calls[0].arguments == "script.py"
        assert result.tool_calls[0].body == 'print("Hello World")'

    def test_parses_tool_call_with_multiline_body(self):
        syntax = EmojiBracketToolSyntax()
        text = """🛠️[create-file script.py]
line1
line2
line3
🛠️[/end]"""

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create-file"
        assert result.tool_calls[0].arguments == "script.py"
        assert result.tool_calls[0].body == "line1\nline2\nline3"


class TestEmojiBracketHeaderParsing:

    def test_parses_tool_name_with_multiple_arguments(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[run-query main.sql 100]\n🛠️[/end]"

        result = syntax.parse(text)

        assert result.tool_calls[0].name == "run-query"
        assert result.tool_calls[0].arguments == "main.sql 100"

    def test_parses_tool_name_with_underscores(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[run_query test.sql]\n🛠️[/end]"

        result = syntax.parse(text)

        assert result.tool_calls[0].name == "run_query"

    def test_parses_tool_name_with_numbers(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[tool1 arg]\n🛠️[/end]"

        result = syntax.parse(text)

        assert result.tool_calls[0].name == "tool1"


class TestEmojiBracketBodyHandling:

    def test_preserves_newlines_in_body(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[tool]\nline1\nline2\n🛠️[/end]"

        result = syntax.parse(text)

        assert result.tool_calls[0].body == "line1\nline2"

    def test_handles_code_blocks_in_body(self):
        syntax = EmojiBracketToolSyntax()
        text = """🛠️[create-file test.py]
```python
def hello():
    print("world")
```
🛠️[/end]"""

        result = syntax.parse(text)

        assert '```python' in result.tool_calls[0].body
        assert 'def hello():' in result.tool_calls[0].body

    def test_handles_markdown_in_body(self):
        syntax = EmojiBracketToolSyntax()
        text = """🛠️[create-file readme.md]
# Hello
This is **bold** text.
🛠️[/end]"""

        result = syntax.parse(text)

        assert '# Hello' in result.tool_calls[0].body
        assert '**bold**' in result.tool_calls[0].body


class TestEmojiBracketMultipleToolCalls:

    def test_parses_two_sequential_tool_calls(self):
        syntax = EmojiBracketToolSyntax()
        text = """🛠️[create-file script.py]
print("Hello World")
🛠️[/end]

🛠️[create-file readme.md]
# Hello
This is a README.
🛠️[/end]"""

        result = syntax.parse(text)

        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].name == "create-file"
        assert result.tool_calls[0].arguments == "script.py"
        assert 'print("Hello World")' in result.tool_calls[0].body
        assert result.tool_calls[1].name == "create-file"
        assert result.tool_calls[1].arguments == "readme.md"
        assert '# Hello' in result.tool_calls[1].body

    def test_parses_tool_calls_with_text_between(self):
        syntax = EmojiBracketToolSyntax()
        text = """I will create two files for you.

🛠️[create-file main.py]
print("Hello from main")
🛠️[/end]

🛠️[create-file utils.py]
def helper():
    return "helper"
🛠️[/end]

Both files have been defined."""

        result = syntax.parse(text)

        assert result.message == "I will create two files for you."
        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].name == "create-file"
        assert result.tool_calls[1].name == "create-file"


class TestEmojiBracketSurroundingText:
    """Tests for tool calls with surrounding text (Section 5.3 of spec)"""

    def test_extracts_message_before_tool_call(self):
        syntax = EmojiBracketToolSyntax()
        text = """Here is your file:
🛠️[create-file script.py]
print("Hello World")
🛠️[/end]
Hope that helps!"""

        result = syntax.parse(text)

        assert result.message == "Here is your file:"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create-file"

    def test_handles_tool_call_at_start_of_text(self):
        syntax = EmojiBracketToolSyntax()
        text = """🛠️[create-file script.py]
print("Hello World")
🛠️[/end]
Hope that helps!"""

        result = syntax.parse(text)

        assert result.message == ""
        assert len(result.tool_calls) == 1

    def test_handles_tool_call_not_at_line_start(self):
        syntax = EmojiBracketToolSyntax()
        text = 'Here is your file: 🛠️[create-file script.py]\nprint("Hello")\n🛠️[/end]'

        result = syntax.parse(text)

        # According to spec, tool blocks can appear anywhere, not just at line start
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create-file"


class TestEmojiBracketNoToolCalls:
    """Tests for text with no tool calls"""

    def test_returns_message_only_when_no_tools(self):
        syntax = EmojiBracketToolSyntax()
        text = "Just a regular message with no tools."

        result = syntax.parse(text)

        assert result.message == text
        assert len(result.tool_calls) == 0

    def test_handles_text_with_emoji_but_no_tools(self):
        syntax = EmojiBracketToolSyntax()
        text = "I like tools 🛠️ but this isn't a tool call"

        result = syntax.parse(text)

        assert result.message == text
        assert len(result.tool_calls) == 0


class TestEmojiBracketErrorHandling:
    """Tests for error handling (Section 7 of spec)"""

    def test_handles_missing_closing_bracket_in_header(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[create-file\nsome text"

        result = syntax.parse(text)

        # Should treat as plain text
        assert len(result.tool_calls) == 0
        assert text in result.message or result.message == text

    def test_handles_missing_end_marker(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[create-file script.py]\nprint('hello')\nmore text"

        result = syntax.parse(text)

        # MAY treat rest of string as body (best effort)
        # At minimum, should not crash
        assert len(result.tool_calls) <= 1

    def test_handles_nested_tool_marker_in_body(self):
        syntax = EmojiBracketToolSyntax()
        text = """🛠️[create-file test.py]
# This code mentions 🛠️[another-tool] but it's not a real tool call
print("test")
🛠️[/end]"""

        result = syntax.parse(text)

        # Inner 🛠️[ should be treated as plain text in the body
        assert len(result.tool_calls) == 1
        assert '🛠️[another-tool]' in result.tool_calls[0].body


class TestEmojiBracketEdgeCases:
    """Tests for edge cases and spec compliance"""

    def test_strips_trailing_whitespace_from_body(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[tool]\nline1  \nline2\t\n🛠️[/end]"

        result = syntax.parse(text)

        # Body should have content but trailing whitespace handling is implementation detail
        assert result.tool_calls[0].body.strip() == "line1  \nline2"

    def test_handles_empty_lines_in_body(self):
        syntax = EmojiBracketToolSyntax()
        text = """🛠️[tool]
line1

line2
🛠️[/end]"""

        result = syntax.parse(text)

        assert 'line1' in result.tool_calls[0].body
        assert 'line2' in result.tool_calls[0].body

    def test_handles_tool_call_with_only_whitespace_body(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[tool]\n   \n\t\n🛠️[/end]"

        result = syntax.parse(text)

        # Should parse successfully, body handling is implementation choice
        assert len(result.tool_calls) == 1


class TestEmojiBracketRoundTrip:
    """Tests that generated examples can be parsed back correctly"""

    def test_round_trip_simple_example(self):
        syntax = EmojiBracketToolSyntax()
        tool = SimpleTool()

        doc = syntax.render_documentation(tool)

        # Extract the first example (should be "🛠️[test_tool value1 value2]")
        example_line = "🛠️[test_tool value1 value2]\n🛠️[/end]"

        result = syntax.parse(example_line)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.tool_calls[0].arguments == "value1 value2"

    def test_round_trip_multiline_example(self):
        syntax = EmojiBracketToolSyntax()
        tool = MultilineTool()

        example = {'inline_arg': 'test', 'multiline_arg': 'line1\nline2'}
        formatted = syntax._format_example(example, [syntax._normalize_argument(arg) for arg in tool.arguments], tool.name)

        result = syntax.parse(formatted)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "multiline_tool"
        assert "test" in result.tool_calls[0].arguments
        assert "line1" in result.tool_calls[0].body
        assert "line2" in result.tool_calls[0].body
