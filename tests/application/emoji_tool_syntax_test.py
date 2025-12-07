"""Tests for tool syntax abstraction."""

from simple_agent.application.tool_syntax import EmojiToolSyntax
from simple_agent.tools.base_tool import BaseTool, ToolArgument


class SimpleTool(BaseTool):
    """Simple test tool with basic configuration."""
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
    """Tool with multiline argument."""
    name = 'multiline_tool'
    description = 'Tool with multiline input'
    arguments = [
        ToolArgument(name='inline_arg', description='Inline argument', required=True),
        ToolArgument(name='multiline_arg', description='Multiline content', required=True, multiline=True),
    ]
    examples = [
        {'inline_arg': 'test', 'multiline_arg': 'line1\nline2\nline3'},
    ]


class TestEmojiToolSyntaxDocumentation:
    """Tests for EmojiToolSyntax.render_documentation()."""

    def test_renders_simple_tool_documentation(self):
        """Test rendering documentation for a simple tool."""
        syntax = EmojiToolSyntax()
        tool = SimpleTool()

        doc = syntax.render_documentation(tool)

        assert 'Tool: test_tool' in doc
        assert 'Description: A test tool' in doc
        assert 'Arguments:' in doc
        assert 'arg1: string (required) - First argument' in doc
        assert 'arg2: string (optional) - Second argument' in doc
        assert 'Usage: 🛠️ test_tool <arg1> [arg2]' in doc
        assert 'Examples:' in doc
        assert '🛠️ test_tool value1 value2' in doc
        assert '🛠️ test_tool only_required' in doc

    def test_renders_multiline_tool_documentation(self):
        """Test rendering documentation with multiline examples."""
        syntax = EmojiToolSyntax()
        tool = MultilineTool()

        doc = syntax.render_documentation(tool)

        assert 'Tool: multiline_tool' in doc
        assert 'Usage: 🛠️ multiline_tool <inline_arg> <multiline_arg>' in doc
        assert '🛠️ multiline_tool test' in doc
        assert 'line1\nline2\nline3' in doc
        assert '🛠️🔚' in doc

    def test_renders_tool_without_arguments(self):
        """Test rendering documentation for a tool with no arguments."""
        class NoArgsTool(BaseTool):
            name = 'no_args'
            description = 'Tool without arguments'
            arguments = []
            examples = []

        syntax = EmojiToolSyntax()
        tool = NoArgsTool()

        doc = syntax.render_documentation(tool)

        assert 'Tool: no_args' in doc
        assert 'Description: Tool without arguments' in doc
        # Should not have Arguments or Usage sections
        assert 'Arguments:' not in doc


class TestEmojiToolSyntaxParsing:
    """Tests for EmojiToolSyntax.parse()."""

    def test_parses_simple_tool_call(self):
        """Test parsing a simple tool call."""
        syntax = EmojiToolSyntax()
        text = "Some message\n🛠️ test_tool arg1 arg2"

        result = syntax.parse(text)

        assert result.message == "Some message"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.tool_calls[0].arguments == "arg1 arg2"

    def test_parses_tool_call_without_message(self):
        """Test parsing tool call at the beginning."""
        syntax = EmojiToolSyntax()
        text = "🛠️ test_tool arg1 arg2"

        result = syntax.parse(text)

        assert result.message == ""
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.tool_calls[0].arguments == "arg1 arg2"

    def test_parses_multiline_tool_call(self):
        """Test parsing a multiline tool call."""
        syntax = EmojiToolSyntax()
        text = """Message here
🛠️ multiline_tool inline_arg
line1
line2
line3
🛠️🔚"""

        result = syntax.parse(text)

        assert result.message == "Message here"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "multiline_tool"
        assert result.tool_calls[0].arguments == "inline_arg\nline1\nline2\nline3"

    def test_parses_multiple_tool_calls(self):
        """Test parsing multiple tool calls."""
        syntax = EmojiToolSyntax()
        text = """Message
🛠️ tool1 arg1
🛠️ tool2 arg2 arg3"""

        result = syntax.parse(text)

        assert result.message == "Message"
        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].name == "tool1"
        assert result.tool_calls[0].arguments == "arg1"
        assert result.tool_calls[1].name == "tool2"
        assert result.tool_calls[1].arguments == "arg2 arg3"

    def test_parses_tool_call_without_arguments(self):
        """Test parsing a tool call with no arguments."""
        syntax = EmojiToolSyntax()
        text = "🛠️ no_args_tool"

        result = syntax.parse(text)

        assert result.message == ""
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "no_args_tool"
        assert result.tool_calls[0].arguments == ""

    def test_returns_message_only_when_no_tools(self):
        """Test parsing text without any tool calls."""
        syntax = EmojiToolSyntax()
        text = "Just a regular message"

        result = syntax.parse(text)

        assert result.message == text
        assert len(result.tool_calls) == 0

    def test_parses_tool_with_hyphenated_name(self):
        """Test parsing tool with hyphenated name."""
        syntax = EmojiToolSyntax()
        text = "🛠️ tool-with-hyphens arg1"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "tool-with-hyphens"
        assert result.tool_calls[0].arguments == "arg1"


class TestEmojiToolSyntaxRoundTrip:
    """Tests that verify formatting and parsing work together."""

    def test_round_trip_simple_example(self):
        """Test that formatted examples can be parsed back."""
        syntax = EmojiToolSyntax()
        tool = SimpleTool()

        # Get documentation which includes formatted examples
        doc = syntax.render_documentation(tool)

        # Extract an example line
        example_line = "🛠️ test_tool value1 value2"

        # Parse it
        result = syntax.parse(example_line)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.tool_calls[0].arguments == "value1 value2"

    def test_round_trip_multiline_example(self):
        """Test that multiline formatted examples can be parsed back."""
        syntax = EmojiToolSyntax()
        tool = MultilineTool()

        # Format an example
        example = {'inline_arg': 'test', 'multiline_arg': 'line1\nline2'}
        formatted = syntax._format_example(example, [syntax._normalize_argument(arg) for arg in tool.arguments], tool.name)

        # Parse it
        result = syntax.parse(formatted)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "multiline_tool"
        assert "test" in result.tool_calls[0].arguments
        assert "line1" in result.tool_calls[0].arguments
        assert "line2" in result.tool_calls[0].arguments
