import textwrap


def test_parse_tool_with_cat_command(tool_library):
    text = "🛠️[cat test.txt]"

    turn = tool_library.parse_and_resolve(text)

    assert turn.message == ""
    assert turn.tool_calls[0] is not None
    assert turn.tool_calls[0].name == "cat"
    assert turn.tool_calls[0].raw_call.named_arguments.get("filename", "") == "test.txt"
    assert type(turn.tool_calls[0].tool_instance).__name__ == "CatTool"


def test_parse_tool_with_message_and_cat_command(tool_library):
    text = dedent("""
    I will read test.txt

    🛠️[cat test.txt]
    """)

    turn = tool_library.parse_and_resolve(text)

    assert turn.message == "I will read test.txt"
    assert turn.tool_calls[0] is not None
    assert turn.tool_calls[0].name == "cat"
    assert turn.tool_calls[0].raw_call.named_arguments.get("filename", "") == "test.txt"
    assert type(turn.tool_calls[0].tool_instance).__name__ == "CatTool"


def test_parse_tool_with_multiline_message_and_ls_command(tool_library):
    text = dedent("""
    Let me read
    the current folder

    🛠️[ls]
    """)

    turn = tool_library.parse_and_resolve(text)

    assert turn.message == dedent("""
    Let me read
    the current folder
    """)
    assert turn.tool_calls[0] is not None
    assert turn.tool_calls[0].name == "ls"
    assert turn.tool_calls[0].raw_call.named_arguments.get("filename", "") == ""
    assert type(turn.tool_calls[0].tool_instance).__name__ == "LsTool"


def test_parse_tool_with_message_and_two_tool_calls(tool_library):
    text = dedent("""
    I will run ls and read test.txt

    🛠️[ls /]
    🛠️[cat test.txt /]
    """)

    turn = tool_library.parse_and_resolve(text)

    assert turn.message == "I will run ls and read test.txt"
    assert turn.tool_calls[0] is not None
    assert turn.tool_calls[0].name == "ls"
    assert turn.tool_calls[0].raw_call.named_arguments.get("filename", "") == ""
    assert type(turn.tool_calls[0].tool_instance).__name__ == "LsTool"
    assert turn.tool_calls[1] is not None
    assert turn.tool_calls[1].name == "cat"
    assert turn.tool_calls[1].raw_call.named_arguments.get("filename", "") == "test.txt"
    assert type(turn.tool_calls[1].tool_instance).__name__ == "CatTool"


def test_parse_tool_with_create_file_multiline(tool_library):
    text = dedent("""
    I will create a file with 3 lines

    🛠️[create-file test.txt]
    Line 1
    Line 2
    Line 3
    🛠️[/end]
    """)

    turn = tool_library.parse_and_resolve(text)

    assert turn.message == "I will create a file with 3 lines"
    assert turn.tool_calls[0] is not None
    assert turn.tool_calls[0].name == "create-file"
    assert turn.tool_calls[0].raw_call.named_arguments.get("filename", "") == "test.txt"
    assert (
        turn.tool_calls[0].raw_call.named_arguments["content"]
        == "Line 1\nLine 2\nLine 3"
    )
    assert type(turn.tool_calls[0].tool_instance).__name__ == "CreateFileTool"


def test_parse_tool_with_create_file_goes_til_end(tool_library):
    text = dedent("""
    I will create a file with 3 lines

    🛠️[create-file test.txt]
    Line 1
    Line 2
    Line 3
    """)

    turn = tool_library.parse_and_resolve(text)

    assert turn.message == "I will create a file with 3 lines"
    assert turn.tool_calls[0] is not None
    assert turn.tool_calls[0].name == "create-file"
    assert turn.tool_calls[0].raw_call.named_arguments.get("filename", "") == "test.txt"
    assert (
        turn.tool_calls[0].raw_call.named_arguments["content"]
        == "Line 1\nLine 2\nLine 3"
    )
    assert type(turn.tool_calls[0].tool_instance).__name__ == "CreateFileTool"


def test_parse_tool_with_multiline_and_message_after(tool_library):
    text = dedent("""
    I will create a file

    🛠️[create-file test.txt]
    Line 1
    Line 2
    🛠️[/end]

    This is text after the tool
    """)

    turn = tool_library.parse_and_resolve(text)

    assert turn.message == "I will create a file"
    assert turn.tool_calls[0] is not None
    assert turn.tool_calls[0].name == "create-file"
    assert turn.tool_calls[0].raw_call.named_arguments.get("filename", "") == "test.txt"
    assert turn.tool_calls[0].raw_call.named_arguments["content"] == "Line 1\nLine 2"
    assert type(turn.tool_calls[0].tool_instance).__name__ == "CreateFileTool"


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

    turn = tool_library.parse_and_resolve(text)

    assert turn.message == "I will create two files"
    assert len(turn.tool_calls) == 2
    assert turn.tool_calls[0].name == "create-file"
    assert (
        turn.tool_calls[0].raw_call.named_arguments.get("filename", "") == "first.txt"
    )
    assert turn.tool_calls[0].raw_call.named_arguments["content"] == "First line"
    assert turn.tool_calls[1].name == "create-file"
    assert (
        turn.tool_calls[1].raw_call.named_arguments.get("filename", "") == "second.txt"
    )
    assert turn.tool_calls[1].raw_call.named_arguments["content"] == "Second line"


def dedent(text):
    return textwrap.dedent(text).strip()


def test_resolving_binds_positional_arguments_to_names(tool_library):
    text = "🛠️[cat 'my notes.md' 1-5]"

    turn = tool_library.parse_and_resolve(text)

    assert turn.tool_calls[0].raw_call.named_arguments == {
        "filename": "my notes.md",
        "line_range": "1-5",
    }


def test_resolving_pairs_a_bound_call_with_its_tool_and_leaves_the_call_as_it_is(
    tool_library,
):
    from simple_agent.application.tool_library import RawToolCall

    bound = RawToolCall("cat", {"filename": "my notes.md"}).bind(
        tool_library.tool_dict["cat"]
    )

    turn = tool_library.resolve_tool_calls([bound], "reading")

    assert turn.message == "reading"
    assert turn.tool_calls[0].raw_call is bound
    assert type(turn.tool_calls[0].tool_instance).__name__ == "CatTool"
