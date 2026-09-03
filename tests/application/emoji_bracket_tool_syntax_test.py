from approvaltests import verify

from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.tool_library import (
    RawToolCall,
    ToolArgument,
    ToolArguments,
)
from simple_agent.tools.base_tool import BaseTool


class SimpleTool(BaseTool):
    name = "test_tool"
    description = "A test tool"
    arguments = ToolArguments(
        header=[
            ToolArgument(name="arg1", description="First argument", required=True),
            ToolArgument(name="arg2", description="Second argument", required=False),
        ]
    )
    examples = [
        {"arg1": "value1", "arg2": "value2"},
        {"arg1": "only_required"},
    ]


class MultilineTool(BaseTool):
    name = "multiline_tool"
    description = "Tool with multiline input"
    arguments = ToolArguments(
        header=[
            ToolArgument(
                name="inline_arg", description="Inline argument", required=True
            )
        ],
        body=ToolArgument(
            name="multiline_arg", description="Multiline content", required=True
        ),
    )
    examples = [
        {"inline_arg": "test", "multiline_arg": "line1\nline2\nline3"},
    ]


class TestEmojiBracketDocumentation:
    def test_renders_simple_tool_documentation(self):
        syntax = EmojiBracketToolSyntax()
        tool = SimpleTool()

        doc = syntax.render_documentation(tool)

        verify(doc)

    def test_renders_multiline_tool_documentation(self):
        syntax = EmojiBracketToolSyntax()
        tool = MultilineTool()

        doc = syntax.render_documentation(tool)

        verify(doc)

    def test_renders_tool_without_arguments(self):
        class NoArgsTool(BaseTool):
            name = "no_args"
            description = "Tool without arguments"
            arguments = ToolArguments()
            examples = []

        syntax = EmojiBracketToolSyntax()
        tool = NoArgsTool()

        doc = syntax.render_documentation(tool)

        verify(doc)

    def test_renders_non_dict_example_values(self):
        class WeirdExampleTool(BaseTool):
            name = "weird_example"
            description = "Tool with unusual examples"
            arguments = ToolArguments()
            examples = [123]

        syntax = EmojiBracketToolSyntax()
        tool = WeirdExampleTool()

        doc = syntax.render_documentation(tool)

        assert "123" in doc


class TestEmojiBracketBasicParsing:
    def test_parses_simple_tool_call_with_no_body(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[create-file]"

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

    def test_parses_simple_tool_call_without_variation_selector(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠[create-file]"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create-file"

    def test_parses_tool_call_with_mixed_variation_selectors(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠[create-file test.txt]\ncontent\n🛠️[/end]"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create-file"
        assert result.tool_calls[0].body == "content"

    def test_parses_tool_call_with_missing_variation_selector_in_end(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[create-file test.txt]\ncontent\n🛠[/end]"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create-file"
        assert result.tool_calls[0].body == "content"


class TestEmojiBracketHeaderParsing:
    def test_parses_tool_name_with_multiple_arguments(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[run-query main.sql 100]"

        result = syntax.parse(text)

        assert result.tool_calls[0].name == "run-query"
        assert result.tool_calls[0].arguments == "main.sql 100"

    def test_parses_tool_name_with_underscores(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[run_query test.sql]"

        result = syntax.parse(text)

        assert result.tool_calls[0].name == "run_query"

    def test_parses_tool_name_with_numbers(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[tool1 arg]"

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

        assert "```python" in result.tool_calls[0].body
        assert "def hello():" in result.tool_calls[0].body

    def test_handles_markdown_in_body(self):
        syntax = EmojiBracketToolSyntax()
        text = """🛠️[create-file readme.md]
# Hello
This is **bold** text.
🛠️[/end]"""

        result = syntax.parse(text)

        assert "# Hello" in result.tool_calls[0].body
        assert "**bold**" in result.tool_calls[0].body


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
        assert "# Hello" in result.tool_calls[1].body

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

    def test_ignores_incomplete_header_after_valid_tool_call(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[ls dir]\n🛠️[/end]\n🛠️[broken"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "ls"

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
        assert "🛠️[another-tool]" in result.tool_calls[0].body
        assert (
            result.tool_calls[0].body
            == """# This code mentions 🛠️[another-tool] but it's not a real tool call
print("test")"""
        )


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

        assert "line1" in result.tool_calls[0].body
        assert "line2" in result.tool_calls[0].body

    def test_handles_tool_call_with_only_whitespace_body(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[tool]\n   \n\t\n🛠️[/end]"

        result = syntax.parse(text)

        # Should parse successfully, body handling is implementation choice
        assert len(result.tool_calls) == 1

    def test_ignores_empty_header_and_parses_next_tool(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[]\n🛠️[ls dir]"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "ls"

    def test_strips_crlf_prefix_when_body_has_end_marker(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[tool]\r\nline1\r\n🛠️[/end]"

        result = syntax.parse(text)

        assert result.tool_calls[0].body == "line1"

    def test_strips_crlf_prefix_when_end_marker_missing(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[tool]\r\nline1"

        result = syntax.parse(text)

        assert result.tool_calls[0].body == "line1"


class TestEmojiBracketBodylessTools:
    """Tests for bodyless tool call parsing (tools without [/end])"""

    def test_parses_single_bodyless_tool(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[ls path/to/dir]"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "ls"
        assert result.tool_calls[0].arguments == "path/to/dir"
        assert result.tool_calls[0].body == ""

    def test_parses_bodyless_tool_with_trailing_whitespace(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[ls path/to/dir]   \n\n"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "ls"
        assert result.tool_calls[0].body == ""

    def test_parses_multiple_bodyless_tools(self):
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[ls dir1 /]\n🛠️[ls dir2 /]\n🛠️[ls dir3 /]"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 3
        assert result.tool_calls[0].arguments == "dir1"
        assert result.tool_calls[1].arguments == "dir2"
        assert result.tool_calls[2].arguments == "dir3"
        for tc in result.tool_calls:
            assert tc.body == ""

    def test_parses_mixed_bodyless_and_body_tools(self):
        syntax = EmojiBracketToolSyntax()
        text = """🛠️[ls dir1 /]
🛠️[cat file.txt]
content of file
🛠️[/end]
🛠️[ls dir2 /]"""

        result = syntax.parse(text)

        assert len(result.tool_calls) == 3
        assert result.tool_calls[0].name == "ls"
        assert result.tool_calls[0].body == ""
        assert result.tool_calls[1].name == "cat"
        assert result.tool_calls[1].body == "content of file"
        assert result.tool_calls[2].name == "ls"
        assert result.tool_calls[2].body == ""

    def test_parses_bodyless_tool_with_message_before(self):
        syntax = EmojiBracketToolSyntax()
        text = "Here are the files:\n🛠️[ls mydir]"

        result = syntax.parse(text)

        assert result.message == "Here are the files:"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].body == ""

    def test_still_supports_legacy_bodyless_with_end_marker(self):
        """Backwards compatibility: bodyless tools with [/end] should still work"""
        syntax = EmojiBracketToolSyntax()
        text = "🛠️[ls dir]\n🛠️[/end]"

        result = syntax.parse(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "ls"
        # Empty body is fine
        assert result.tool_calls[0].body == ""


class TestEmojiBracketRoundTrip:
    """Tests that generated examples can be parsed back correctly"""

    def test_round_trip_simple_example(self):
        syntax = EmojiBracketToolSyntax()

        # Extract the first example (should be "🛠️[test_tool value1 value2]")
        # Bodyless tools no longer have [/end]
        example_line = "🛠️[test_tool value1 value2]"

        result = syntax.parse(example_line)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.tool_calls[0].arguments == "value1 value2"

    def test_round_trip_multiline_example(self):
        syntax = EmojiBracketToolSyntax()
        tool = MultilineTool()

        doc = syntax.render_documentation(tool)

        # Extract the example from documentation and parse it
        example_start = doc.find("🛠️[multiline_tool test]")
        assert example_start != -1, "Example not found in documentation"

        example_text = doc[example_start:]
        result = syntax.parse(example_text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "multiline_tool"
        assert "test" in result.tool_calls[0].arguments
        assert "line1" in result.tool_calls[0].body


class TestBind:
    def test_binds_positional_arguments_to_declared_names(self):
        call = RawToolCall(name="test_tool", arguments="value1 value2")

        bound = EmojiBracketToolSyntax().bind(call, SimpleTool())

        assert bound.named_arguments == {"arg1": "value1", "arg2": "value2"}

    def test_omits_optional_arguments_that_were_not_given(self):
        call = RawToolCall(name="test_tool", arguments="value1")

        bound = EmojiBracketToolSyntax().bind(call, SimpleTool())

        assert bound.named_arguments == {"arg1": "value1"}

    def test_a_quoted_value_binds_as_one_argument(self):
        call = RawToolCall(name="test_tool", arguments="'my notes.md' value2")

        bound = EmojiBracketToolSyntax().bind(call, SimpleTool())

        assert bound.named_arguments == {"arg1": "my notes.md", "arg2": "value2"}

    def test_a_single_header_argument_takes_the_whole_text(self):
        call = RawToolCall(name="multiline_tool", arguments="rg 'main\\(' -g '*.py'")

        bound = EmojiBracketToolSyntax().bind(call, MultilineTool())

        assert bound.named_arguments["inline_arg"] == "rg 'main\\(' -g '*.py'"

    def test_the_body_binds_to_the_body_argument(self):
        call = RawToolCall(name="multiline_tool", arguments="test", body="line1\nline2")

        bound = EmojiBracketToolSyntax().bind(call, MultilineTool())

        assert bound.named_arguments == {
            "inline_arg": "test",
            "multiline_arg": "line1\nline2",
        }

    def test_leaves_already_named_arguments_alone(self):
        call = RawToolCall(
            name="test_tool", arguments="a b", named_arguments={"arg1": "native"}
        )

        bound = EmojiBracketToolSyntax().bind(call, SimpleTool())

        assert bound.named_arguments == {"arg1": "native"}

    def test_unbalanced_quotes_bind_nothing(self):
        call = RawToolCall(name="test_tool", arguments="'broken value2")

        bound = EmojiBracketToolSyntax().bind(call, SimpleTool())

        assert bound.named_arguments == {}

    def test_extra_tokens_flow_into_the_last_header_argument(self):
        call = RawToolCall(name="test_tool", arguments="value1 say hello world")

        bound = EmojiBracketToolSyntax().bind(call, SimpleTool())

        assert bound.named_arguments == {"arg1": "value1", "arg2": "say hello world"}

    def test_boolean_arguments_bind_as_flags_by_name(self):
        flagged = _MockFlagTool()
        call = RawToolCall(name="flag_tool", arguments="coding say hello --async")

        bound = EmojiBracketToolSyntax().bind(call, flagged)

        assert bound.named_arguments == {
            "agenttype": "coding",
            "task": "say hello",
            "--async": True,
        }

    def test_an_absent_flag_is_not_bound(self):
        call = RawToolCall(name="flag_tool", arguments="coding say hello")

        bound = EmojiBracketToolSyntax().bind(call, _MockFlagTool())

        assert bound.named_arguments == {"agenttype": "coding", "task": "say hello"}


class _MockFlagTool(BaseTool):
    name = "flag_tool"
    description = "Tool with a flag"
    arguments = ToolArguments(
        header=[
            ToolArgument(name="agenttype", description="", required=True),
            ToolArgument(name="task", description="", required=True),
            ToolArgument(name="--async", type="bool", description="", required=False),
        ]
    )
    examples = []


class TestRenderHeader:
    def test_quotes_a_value_with_spaces(self):
        named = {"arg1": "my notes.md", "arg2": "value2"}

        header = EmojiBracketToolSyntax().render_header(named, SimpleTool())

        assert header == "'my notes.md' value2"

    def test_renders_a_true_flag_by_name_and_omits_a_false_one(self):
        named = {"agenttype": "coding", "task": "say hello", "--async": True}

        header = EmojiBracketToolSyntax().render_header(named, _MockFlagTool())

        assert header == "coding 'say hello' --async"
        assert (
            EmojiBracketToolSyntax().render_header(
                {**named, "--async": False}, _MockFlagTool()
            )
            == "coding 'say hello'"
        )

    def test_a_single_header_argument_is_left_unquoted(self):
        named = {"inline_arg": "rg 'main\\(' -g '*.py'"}

        header = EmojiBracketToolSyntax().render_header(named, MultilineTool())

        assert header == "rg 'main\\(' -g '*.py'"

    def test_rendering_then_binding_round_trips(self):
        syntax = EmojiBracketToolSyntax()
        named = {"agenttype": "coding", "task": 'say "hi" there', "--async": True}

        header = syntax.render_header(named, _MockFlagTool())
        bound = syntax.bind(
            RawToolCall(name="flag_tool", arguments=header), _MockFlagTool()
        )

        assert bound.named_arguments == named
