import textwrap

from simple_agent.tools.all_tools import AllTools

library = AllTools()


def test_parse_tool_with_cat_command():
    text = "🛠️ cat test.txt"

    message_and_tools = library.parse_tool(text)

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

    message_and_tools = library.parse_tool(text)

    assert message_and_tools.message == "I will read test.txt"
    assert message_and_tools.tools[0] is not None
    assert message_and_tools.tools[0].name == "cat"
    assert message_and_tools.tools[0].arguments == "test.txt"
    assert type(message_and_tools.tools[0].tool_instance).__name__ == "CatTool"


def dedent(text):
    return textwrap.dedent(text).strip()
