from approvaltests import verify
from simple_agent.application.tool_library import RawToolCall
from simple_agent.tools.replace_content_tool import ReplaceContentTool

def test_replace_content_replace(tmp_path):
    # Create a dummy file in the temporary directory
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello, world!\\nThis is a test file.\\n")

    # Get the "before" state of the file
    before_content = file_path.read_text()

    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments=str(file_path),
        body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
    )
    result = tool.execute(raw_call)

    # Get the "after" state of the file
    after_content = file_path.read_text()

    verify(f"BEFORE:\\n{before_content}\\nAFTER:\\n{after_content}\\nRESULT:\\n{result.message}")

def test_replace_content_insert(tmp_path):
    # Create a dummy file in the temporary directory
    file_path = tmp_path / "test.txt"
    file_path.write_text("Line 1\\nLine 3\\n")

    # Get the "before" state of the file
    before_content = file_path.read_text()

    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments=str(file_path),
        body="""<<<<<<< SEARCH
Line 1
=======
Line 1
Line 2
>>>>>>> REPLACE
"""
    )
    result = tool.execute(raw_call)

    # Get the "after" state of the file
    after_content = file_path.read_text()

    verify(f"BEFORE:\\n{before_content}\\nAFTER:\\n{after_content}\\nRESULT:\\n{result.message}")

def test_replace_content_delete(tmp_path):
    # Create a dummy file in the temporary directory
    file_path = tmp_path / "test.txt"
    file_path.write_text("Line 1\\nLine 2\\nLine 3\\n")

    # Get the "before" state of the file
    before_content = file_path.read_text()

    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments=str(file_path),
        body="""<<<<<<< SEARCH
Line 2
=======
>>>>>>> REPLACE
"""
    )
    result = tool.execute(raw_call)

    # Get the "after" state of the file
    after_content = file_path.read_text()

    verify(f"BEFORE:\\n{before_content}\\nAFTER:\\n{after_content}\\nRESULT:\\n{result.message}")

def test_replace_content_not_found(tmp_path):
    file_path = tmp_path / "nonexistent.txt"

    tool = ReplaceContentTool()
    raw_call = RawToolCall(
        name="replace-content",
        arguments=str(file_path),
        body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
    )
    result = tool.execute(raw_call)

    verify(f"RESULT:\\n{result.message}")
