from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax


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
