import textwrap


def test_parse_tool_with_cat_command(tool_library):
    text = "🛠️[cat test.txt]"

    resolved = tool_library.parse_and_resolve(text)

    assert resolved.message == ""
    assert resolved.tool_calls[0] is not None
    assert resolved.tool_calls[0].name == "cat"
    assert resolved.tool_calls[0].arguments == "test.txt"
    assert type(resolved.tool_calls[0].tool_instance).__name__ == "CatTool"


def test_parse_tool_with_message_and_cat_command(tool_library):
    text = dedent("""
    I will read test.txt

    🛠️[cat test.txt]
    """)

    resolved = tool_library.parse_and_resolve(text)

    assert resolved.message == "I will read test.txt"
    assert resolved.tool_calls[0] is not None
    assert resolved.tool_calls[0].name == "cat"
    assert resolved.tool_calls[0].arguments == "test.txt"
    assert type(resolved.tool_calls[0].tool_instance).__name__ == "CatTool"


def test_parse_tool_with_multiline_message_and_ls_command(tool_library):
    text = dedent("""
    Let me read
    the current folder

    🛠️[ls]
    """)

    resolved = tool_library.parse_and_resolve(text)

    assert resolved.message == dedent("""
    Let me read
    the current folder
    """)
    assert resolved.tool_calls[0] is not None
    assert resolved.tool_calls[0].name == "ls"
    assert resolved.tool_calls[0].arguments == ""
    assert type(resolved.tool_calls[0].tool_instance).__name__ == "LsTool"


def test_parse_tool_with_message_and_two_tool_calls(tool_library):
    text = dedent("""
    I will run ls and read test.txt

    🛠️[ls /]
    🛠️[cat test.txt /]
    """)

    resolved = tool_library.parse_and_resolve(text)

    assert resolved.message == "I will run ls and read test.txt"
    assert resolved.tool_calls[0] is not None
    assert resolved.tool_calls[0].name == "ls"
    assert resolved.tool_calls[0].arguments == ""
    assert type(resolved.tool_calls[0].tool_instance).__name__ == "LsTool"
    assert resolved.tool_calls[1] is not None
    assert resolved.tool_calls[1].name == "cat"
    assert resolved.tool_calls[1].arguments == "test.txt"
    assert type(resolved.tool_calls[1].tool_instance).__name__ == "CatTool"


def test_parse_tool_with_create_file_multiline(tool_library):
    text = dedent("""
    I will create a file with 3 lines

    🛠️[create-file test.txt]
    Line 1
    Line 2
    Line 3
    🛠️[/end]
    """)

    resolved = tool_library.parse_and_resolve(text)

    assert resolved.message == "I will create a file with 3 lines"
    assert resolved.tool_calls[0] is not None
    assert resolved.tool_calls[0].name == "create-file"
    assert resolved.tool_calls[0].arguments == "test.txt"
    assert resolved.tool_calls[0].body == "Line 1\nLine 2\nLine 3"
    assert type(resolved.tool_calls[0].tool_instance).__name__ == "CreateFileTool"


def test_parse_tool_with_create_file_goes_til_end(tool_library):
    text = dedent("""
    I will create a file with 3 lines

    🛠️[create-file test.txt]
    Line 1
    Line 2
    Line 3
    """)

    resolved = tool_library.parse_and_resolve(text)

    assert resolved.message == "I will create a file with 3 lines"
    assert resolved.tool_calls[0] is not None
    assert resolved.tool_calls[0].name == "create-file"
    assert resolved.tool_calls[0].arguments == "test.txt"
    assert resolved.tool_calls[0].body == "Line 1\nLine 2\nLine 3"
    assert type(resolved.tool_calls[0].tool_instance).__name__ == "CreateFileTool"


def test_parse_tool_with_multiline_and_message_after(tool_library):
    text = dedent("""
    I will create a file

    🛠️[create-file test.txt]
    Line 1
    Line 2
    🛠️[/end]

    This is text after the tool
    """)

    resolved = tool_library.parse_and_resolve(text)

    assert resolved.message == "I will create a file"
    assert resolved.tool_calls[0] is not None
    assert resolved.tool_calls[0].name == "create-file"
    assert resolved.tool_calls[0].arguments == "test.txt"
    assert resolved.tool_calls[0].body == "Line 1\nLine 2"
    assert type(resolved.tool_calls[0].tool_instance).__name__ == "CreateFileTool"


def test_parse_tool_with_two_multiline_tools(tool_library):
    text = dedent("""
    I will create two files

    🛠️[create-file first.txt]
    First line
    🛠️[/end]
    🛠️[create-file second.txt]
    Second line
    🛠️[/end]
    """)

    resolved = tool_library.parse_and_resolve(text)

    assert resolved.message == "I will create two files"
    assert len(resolved.tool_calls) == 2
    assert resolved.tool_calls[0].name == "create-file"
    assert resolved.tool_calls[0].arguments == "first.txt"
    assert resolved.tool_calls[0].body == "First line"
    assert resolved.tool_calls[1].name == "create-file"
    assert resolved.tool_calls[1].arguments == "second.txt"
    assert resolved.tool_calls[1].body == "Second line"


def dedent(text):
    return textwrap.dedent(text).strip()
