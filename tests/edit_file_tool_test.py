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

def verify_edit_tool(framework, setup_file, setup_content, command, tmp_path=None):
    path_scrubber = create_path_scrubber()
    date_scrubber = create_date_scrubber()
    ls_error_scrubber = create_ls_error_scrubber()
    multi_scrubber = combine_scrubbers(path_scrubber, date_scrubber, ls_error_scrubber)

    def _execute_and_verify():
        # Setup: create the initial file
        with open(setup_file, "w") as f:
            f.write(setup_content)

        # Show initial file content
        initial_file_info = f"Initial file: {setup_file}\nInitial content:\n--- INITIAL CONTENT START ---\n{setup_content}\n--- INITIAL CONTENT END ---"

        # Execute the edit command
        result = framework.parse_and_execute(command)

        # Verify the file was modified correctly
        if os.path.exists(setup_file):
            with open(setup_file, "r") as f:
                actual_content = f.read()
                final_file_info = f"File after edit: {setup_file}\nFinal content:\n--- FINAL CONTENT START ---\n{actual_content}\n--- FINAL CONTENT END ---"
        else:
            final_file_info = "File not found after edit"

        # Create verification output including both initial and final file content
        verify(f"Command:\n{command}\n\nResult:\n{result}\n\n{initial_file_info}\n\n{final_file_info}", options=Options().with_scrubber(multi_scrubber))

    if tmp_path:
        with temp_directory(tmp_path):
            _execute_and_verify()
    else:
        _execute_and_verify()

def test_edit_file_replace_single_character(tmp_path):
    verify_edit_tool(library, "test.txt", "a", "/edit-file test.txt 1 1 b", tmp_path=tmp_path)

def test_edit_file_replace_single_word(tmp_path):
    verify_edit_tool(library, "test.txt", "old", "/edit-file test.txt 1 1 new", tmp_path=tmp_path)

def test_edit_file_replace_two_consecutive_lines_with_one(tmp_path):
    verify_edit_tool(library, "test.txt", "line1\nline2\nline3", "/edit-file test.txt 2 3 newline", tmp_path=tmp_path)

def test_edit_file_replace_two_consecutive_lines_with_two(tmp_path):
    # Use actual newline character in the command, not literal \n
    command = "/edit-file test.txt 2 3 newline1\nnewline2"
    verify_edit_tool(library, "test.txt", "line1\nline2\nline3", command, tmp_path=tmp_path)

def test_edit_file_replace_two_consecutive_lines_with_four(tmp_path):
    # Replace 2 consecutive lines in 3-line file with 4 other lines
    command = "/edit-file test.txt 2 3 newline1\nnewline2\nnewline3\nnewline4"
    verify_edit_tool(library, "test.txt", "line1\nline2\nline3", command, tmp_path=tmp_path)

def test_edit_file_replace_empty_lines_with_function(tmp_path):
    # Replace empty lines 3-5 with function definition
    initial_content = "line1\nline2\n\n\n\nline6"
    function_def = "def hello():\n    return 'world'"
    command = f"/edit-file template.py 3 5 {function_def}"
    expected_content = "line1\nline2\ndef hello():\n    return 'world'\nline6"
    verify_edit_tool(library, "template.py", initial_content, command, tmp_path=tmp_path)

def test_edit_file_add_two_lines_to_empty_file(tmp_path):
    # Test adding content to an empty file using 0-0 range
    command = "/edit-file empty.txt 0 0 line1\\nline2"
    expected_content = "line1\nline2\n"
    verify_edit_tool(library, "empty.txt", "", command, tmp_path=tmp_path)
