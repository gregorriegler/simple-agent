import textwrap

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
    assert result.tool_calls[0].name == "ls"
    assert result.tool_calls[0].arguments == ""
    assert result.tool_calls[1].name == "bash"
    assert result.tool_calls[1].arguments == "pwd"


def test_parse_tool_with_hyphen_in_name():
    text = "🛠️ create-file test.txt\ncontent"
    result = parse_tool_calls(text)
    assert result.tool_calls[0].name == "create-file"
    assert result.tool_calls[0].arguments == "test.txt\ncontent"


def test_parse_tool_with_multiline_message():
    text = dedent("""
    Let me read
    the current folder

    🛠️ ls
    """)
    result = parse_tool_calls(text)
    assert result.message == dedent("""
    Let me read
    the current folder
    """)
    assert result.tool_calls[0].name == "ls"


def test_parse_tool_with_end_marker():
    text = dedent("""
    I will create a file

    🛠️ create-file test.txt
    Line 1
    Line 2
    🛠️🔚

    This is text after the tool
    """)
    result = parse_tool_calls(text)
    assert result.message == "I will create a file"
    assert result.tool_calls[0].name == "create-file"
    assert result.tool_calls[0].arguments == "test.txt\nLine 1\nLine 2"


def test_parse_two_multiline_tools():
    text = dedent("""
    I will create two files

    🛠️ create-file first.txt
    First line
    🛠️🔚
    🛠️ create-file second.txt
    Second line
    🛠️🔚
    """)
    result = parse_tool_calls(text)
    assert result.message == "I will create two files"
    assert len(result.tool_calls) == 2
    assert result.tool_calls[0].name == "create-file"
    assert result.tool_calls[0].arguments == "first.txt\nFirst line"
    assert result.tool_calls[1].name == "create-file"
    assert result.tool_calls[1].arguments == "second.txt\nSecond line"


def test_parse_unknown_tool_returns_raw_call():
    """Parser does not validate tool names - returns raw calls for any tool name."""
    text = "🛠️ nonexistent_tool arg1"
    result = parse_tool_calls(text)
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "nonexistent_tool"
    assert result.tool_calls[0].arguments == "arg1"


def dedent(text):
    return textwrap.dedent(text).strip()
