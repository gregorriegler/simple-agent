import textwrap

from simple_agent.tools.all_tools import AllTools

library = AllTools()


def test_parse_tool_with_cat_command():
    text = "🛠️ cat test.txt"

    message_and_tools = library.parse_message_and_tools(text)

    assert message_and_tools.message == ""
    assert message_and_tools.tools[0] is not None
    assert message_and_tools.tools[0].name == "cat"
    assert message_and_tools.tools[0].arguments == "test.txt"
    assert type(message_and_tools.tools[0].tool_instance).__name__ == "CatTool"


def test_parse_tool_with_message_and_cat_command():
    text = dedent("""
    I will read test.txt

    🛠️ cat test.txt
    """)

    message_and_tools = library.parse_message_and_tools(text)

    assert message_and_tools.message == "I will read test.txt"
    assert message_and_tools.tools[0] is not None
    assert message_and_tools.tools[0].name == "cat"
    assert message_and_tools.tools[0].arguments == "test.txt"
    assert type(message_and_tools.tools[0].tool_instance).__name__ == "CatTool"


def test_parse_tool_with_multiline_message_and_ls_command():
    text = dedent("""
    Let me read
    the current folder

    🛠️ ls
    """)

    message_and_tools = library.parse_message_and_tools(text)

    assert message_and_tools.message == dedent("""
    Let me read
    the current folder
    """)
    assert message_and_tools.tools[0] is not None
    assert message_and_tools.tools[0].name == "ls"
    assert message_and_tools.tools[0].arguments == ""
    assert type(message_and_tools.tools[0].tool_instance).__name__ == "LsTool"

def test_parse_tool_with_message_and_two_tool_calls():
    text = dedent("""
    I will run ls and read test.txt

    🛠️ ls
    🛠️ cat test.txt
    """)

    message_and_tools = library.parse_message_and_tools(text)

    assert message_and_tools.message == "I will run ls and read test.txt"
    assert message_and_tools.tools[0] is not None
    assert message_and_tools.tools[0].name == "ls"
    assert message_and_tools.tools[0].arguments == ""
    assert type(message_and_tools.tools[0].tool_instance).__name__ == "LsTool"
    assert message_and_tools.tools[1] is not None
    assert message_and_tools.tools[1].name == "cat"
    assert message_and_tools.tools[1].arguments == "test.txt"
    assert type(message_and_tools.tools[1].tool_instance).__name__ == "CatTool"


def test_parse_tool_with_create_file_multiline():
    text = dedent("""
    I will create a file with 3 lines

    🛠️ create-file test.txt
    Line 1
    Line 2
    Line 3
    🛠️🔚
    """)

    message_and_tools = library.parse_message_and_tools(text)

    assert message_and_tools.message == "I will create a file with 3 lines"
    assert message_and_tools.tools[0] is not None
    assert message_and_tools.tools[0].name == "create-file"
    assert message_and_tools.tools[0].arguments == "test.txt\nLine 1\nLine 2\nLine 3"
    assert type(message_and_tools.tools[0].tool_instance).__name__ == "CreateFileTool"


def test_parse_tool_with_create_file_goes_til_end():
    text = dedent("""
    I will create a file with 3 lines

    🛠️ create-file test.txt
    Line 1
    Line 2
    Line 3
    """)

    message_and_tools = library.parse_message_and_tools(text)

    assert message_and_tools.message == "I will create a file with 3 lines"
    assert message_and_tools.tools[0] is not None
    assert message_and_tools.tools[0].name == "create-file"
    assert message_and_tools.tools[0].arguments == "test.txt\nLine 1\nLine 2\nLine 3"
    assert type(message_and_tools.tools[0].tool_instance).__name__ == "CreateFileTool"


def test_parse_tool_with_multiline_and_message_after():
    text = dedent("""
    I will create a file

    🛠️ create-file test.txt
    Line 1
    Line 2
    🛠️🔚

    This is text after the tool
    """)

    message_and_tools = library.parse_message_and_tools(text)

    assert message_and_tools.message == "I will create a file"
    assert message_and_tools.tools[0] is not None
    assert message_and_tools.tools[0].name == "create-file"
    assert message_and_tools.tools[0].arguments == "test.txt\nLine 1\nLine 2"
    assert type(message_and_tools.tools[0].tool_instance).__name__ == "CreateFileTool"


def test_parse_tool_with_two_multiline_tools():
    text = dedent("""
    I will create two files

    🛠️ create-file first.txt
    First line
    🛠️🔚
    🛠️ create-file second.txt
    Second line
    🛠️🔚
    """)

    message_and_tools = library.parse_message_and_tools(text)

    assert message_and_tools.message == "I will create two files"
    assert len(message_and_tools.tools) == 2
    assert message_and_tools.tools[0].name == "create-file"
    assert message_and_tools.tools[0].arguments == "first.txt\nFirst line"
    assert message_and_tools.tools[1].name == "create-file"
    assert message_and_tools.tools[1].arguments == "second.txt\nSecond line"


def dedent(text):
    return textwrap.dedent(text).strip()
