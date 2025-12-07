from simple_agent.application.emoji_tool_syntax import EmojiToolSyntax
from simple_agent.application.tool_message_parser import parse_tool_calls
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
    ]
    body = ToolArgument(name='multiline_arg', description='Multiline content', required=True)
    examples = [
        {'inline_arg': 'test', 'multiline_arg': 'line1\nline2\nline3'},
    ]


class TestEmojiToolSyntaxDocumentation:
    def test_renders_simple_tool_documentation(self):
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
        syntax = EmojiToolSyntax()
        tool = MultilineTool()

        doc = syntax.render_documentation(tool)

        assert 'Tool: multiline_tool' in doc
        assert 'Usage: 🛠️ multiline_tool <inline_arg> <multiline_arg>' in doc
        assert '🛠️ multiline_tool test' in doc
        assert 'line1\nline2\nline3' in doc
        assert '🛠️🔚' in doc

    def test_renders_tool_without_arguments(self):
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
        assert 'Arguments:' not in doc


class TestEmojiToolSyntaxParsing:
    def test_parses_simple_tool_call(self):
        syntax = EmojiToolSyntax()
        text = "Some message\n🛠️ test_tool arg1 arg2"

        result = syntax.parse(text)

        assert result.message == "Some message"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.tool_calls[0].arguments == "arg1 arg2"

    def test_parses_tool_call_without_message(self):
        syntax = EmojiToolSyntax()
        text = "🛠️ test_tool arg1 arg2"

        result = syntax.parse(text)

        assert result.message == ""
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.tool_calls[0].arguments == "arg1 arg2"

    def test_parses_multiline_tool_call(self):
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
        assert result.tool_calls[0].arguments == "inline_arg"
        assert result.tool_calls[0].body == "line1\nline2\nline3"

    def test_parses_multiple_tool_calls(self):
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
        syntax = EmojiToolSyntax()
        text = "🛠️ no_args_tool"

        result = syntax.parse(text)

        assert result.message == ""
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "no_args_tool"
        assert result.tool_calls[0].arguments == ""

    def test_returns_message_only_when_no_tools(self):
        syntax = EmojiToolSyntax()
        text = "Just a regular message"

        result = syntax.parse(text)

        assert result.message == text
        assert len(result.tool_calls) == 0

    def test_parses_tool_with_hyphenated_name(self):
        syntax = EmojiToolSyntax()
        text = "🛠️ tool-with-hyphens arg1"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "tool-with-hyphens"
        assert result.tool_calls[0].arguments == "arg1"


class TestEmojiToolSyntaxCompatibility:
    def test_render_documentation_simple(self):
        syntax = EmojiToolSyntax()
        tool = SimpleTool()

        output = syntax.render_documentation(tool)

        assert output  # Basic smoke test that it returns something

    def test_render_documentation_multiline(self):
        syntax = EmojiToolSyntax()
        tool = MultilineTool()

        output = syntax.render_documentation(tool)

        assert output  # Basic smoke test that it returns something

    def test_render_documentation_no_args(self):
        class NoArgsTool(BaseTool):
            name = 'no_args'
            description = 'Tool without arguments'
            arguments = []
            examples = []

        syntax = EmojiToolSyntax()
        tool = NoArgsTool()

        output = syntax.render_documentation(tool)

        assert output  # Basic smoke test that it returns something

    def test_produces_identical_parsing_to_parse_tool_calls_simple(self):
        syntax = EmojiToolSyntax()
        text = "Some message\n🛠️ test_tool arg1 arg2"

        syntax_result = syntax.parse(text)
        parser_result = parse_tool_calls(text, syntax)

        assert syntax_result == parser_result

    def test_produces_identical_parsing_to_parse_tool_calls_multiline(self):
        syntax = EmojiToolSyntax()
        text = """Message here
🛠️ multiline_tool inline_arg
line1
line2
🛠️🔚"""

        syntax_result = syntax.parse(text)
        parser_result = parse_tool_calls(text, syntax)

        assert syntax_result == parser_result

    def test_produces_identical_parsing_to_parse_tool_calls_multiple(self):
        syntax = EmojiToolSyntax()
        text = """Message
🛠️ tool1 arg1
🛠️ tool2 arg2 arg3"""

        syntax_result = syntax.parse(text)
        parser_result = parse_tool_calls(text, syntax)

        assert syntax_result == parser_result

    def test_produces_identical_parsing_to_parse_tool_calls_no_tools(self):
        syntax = EmojiToolSyntax()
        text = "Just a regular message"

        syntax_result = syntax.parse(text)
        parser_result = parse_tool_calls(text, syntax)

        assert syntax_result == parser_result


class TestEmojiToolSyntaxRoundTrip:
    def test_round_trip_simple_example(self):
        syntax = EmojiToolSyntax()
        tool = SimpleTool()

        doc = syntax.render_documentation(tool)

        example_line = "🛠️ test_tool value1 value2"

        result = syntax.parse(example_line)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.tool_calls[0].arguments == "value1 value2"

    def test_round_trip_multiline_example(self):
        syntax = EmojiToolSyntax()
        tool = MultilineTool()

        example = {'inline_arg': 'test', 'multiline_arg': 'line1\nline2'}
        all_args = list(tool.arguments)
        if tool.body:
            all_args.append(tool.body)
        normalized_args = [syntax._normalize_argument(arg, is_body=(arg == tool.body)) for arg in all_args]
        formatted = syntax._format_example(example, normalized_args, tool.name)

        result = syntax.parse(formatted)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "multiline_tool"
        assert "test" in result.tool_calls[0].arguments
        assert "line1" in result.tool_calls[0].body
        assert "line2" in result.tool_calls[0].body
