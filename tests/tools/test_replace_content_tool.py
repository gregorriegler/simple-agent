import os
from approvaltests import verify
from simple_agent.tools.replace_content_tool import ReplaceContentTool
from simple_agent.application.tool_library import RawToolCall

def test_replace_content_success():
    # Create a dummy file
    with open("test.txt", "w") as f:
        f.write("Hello, world!\\nThis is a test file.\\n")

    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments="test.txt",
        body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
    )
    result = tool.execute(raw_call)

    with open("test.txt", "r") as f:
        content = f.read()

    os.remove("test.txt")

    assert result.success
    assert "Hello, universe!\\nThis is a test file.\\n" == content
    verify(result.message)

def test_replace_content_file_not_found():
    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments="nonexistent.txt",
        body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
    )
    result = tool.execute(raw_call)

    assert not result.success
    verify(result.message)

def test_replace_content_search_content_not_found():
    # Create a dummy file
    with open("test.txt", "w") as f:
        f.write("This is a test file.\\n")

    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments="test.txt",
        body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
    )
    result = tool.execute(raw_call)

    os.remove("test.txt")

    assert not result.success
    verify(result.message)

def test_replace_content_invalid_format():
    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments="test.txt",
        body="""< SEARCH
Hello, world!
---
Hello, universe!
> REPLACE
"""
    )
    result = tool.execute(raw_call)

    assert not result.success
    verify(result.message)

def test_replace_content_empty_search_block():
    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments="test.txt",
        body="""<<<<<<< SEARCH
=======
Hello, universe!
>>>>>>> REPLACE
"""
    )
    result = tool.execute(raw_call)

    assert not result.success
    verify(result.message)

def test_replace_content_replaces_only_first_occurrence():
    # Create a dummy file
    with open("test.txt", "w") as f:
        f.write("Hello, world!\\nHello, world!\\n")

    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments="test.txt",
        body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
    )
    result = tool.execute(raw_call)

    with open("test.txt", "r") as f:
        content = f.read()

    os.remove("test.txt")

    assert result.success
    assert "Hello, universe!\\nHello, world!\\n" == content
    verify(result.message)
