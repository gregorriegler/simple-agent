import os
from contextlib import contextmanager
from approvaltests import Options, verify
from approvaltests.scrubbers import combine_scrubbers

from tools.tool_library import ToolLibrary
from .test_helpers import create_path_scrubber, create_date_scrubber, create_ls_error_scrubber

library = ToolLibrary()

@contextmanager
def temp_directory(tmp_path):
    """Context manager to handle directory changes for tests."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield
    finally:
        os.chdir(original_cwd)

def verify_create_tool(framework, command, expected_filename, expected_content=None, tmp_path=None):
    """
    Verify a create tool command and check the created file's content.

    Args:
        framework: The tool framework to execute the command
        command: The command to execute
        expected_filename: The filename that should be created
        expected_content: The expected content of the file (None for empty file)
        tmp_path: Optional temporary path to change to during execution
    """
    if expected_content is None:
        ""

    # Create scrubber for consistent output
    path_scrubber = create_path_scrubber()
    date_scrubber = create_date_scrubber()
    ls_error_scrubber = create_ls_error_scrubber()
    multi_scrubber = combine_scrubbers(path_scrubber, date_scrubber, ls_error_scrubber)

    def _execute_and_verify():
        result = framework.parse_and_execute(command)

        if expected_filename and not os.path.exists(expected_filename):
            raise AssertionError(f"File '{expected_filename}' should have been created")

        if expected_filename:
            with open(expected_filename, "r") as f:
                actual_content = f.read()
                file_info = f"File created: {expected_filename}\nFile content:\n--- FILE CONTENT START ---\n{actual_content}\n--- FILE CONTENT END ---"
        else:
            file_info = "No File created"

        # Create verification output including file content
        verify(f"Command:\n{command}\n\nResult:\n{result}\n\n{file_info}", options=Options().with_scrubber(multi_scrubber))

    if tmp_path:
        with temp_directory(tmp_path):
            _execute_and_verify()
    else:
        _execute_and_verify()

def test_create_tool_single_character_name(tmp_path):
    verify_create_tool(library, "/create-file a", "a", tmp_path=tmp_path)

def test_create_tool_simple_name_with_extension(tmp_path):
    verify_create_tool(library, "/create-file test.txt", "test.txt", tmp_path=tmp_path)

def test_create_tool_single_character_content(tmp_path):
    verify_create_tool(library, "/create-file test.txt a", "test.txt", "a", tmp_path=tmp_path)

def test_create_tool_simple_text_content(tmp_path):
    verify_create_tool(library, "/create-file readme.txt Hello World", "readme.txt", "Hello World", tmp_path=tmp_path)

def test_create_tool_newline_content(tmp_path):
    verify_create_tool(library, '/create-file multi.txt "Line 1\\nLine 2"', "multi.txt", "Line 1\nLine 2", tmp_path=tmp_path)

def test_create_tool_json_content(tmp_path):
    verify_create_tool(library, '/create-file config.json {"name": "test"}', "config.json", '{"name": "test"}', tmp_path=tmp_path)

def test_create_tool_explicit_empty_content(tmp_path):
    verify_create_tool(library, '/create-file empty.txt ""', "empty.txt", "", tmp_path=tmp_path)

def test_create_file_in_nonexistent_directory(tmp_path):
    verify_create_tool(library, f'/create-file src/utils/helper.py "# Helper module"', "src/utils/helper.py", "# Helper module", tmp_path=tmp_path)

def test_create_file_already_exists(tmp_path):
    with temp_directory(tmp_path):
        library.parse_and_execute("/create-file existing.txt")

        result = library.parse_and_execute("/create-file existing.txt")

        assert 'already exists' in result.lower() or 'exists' in result.lower()
