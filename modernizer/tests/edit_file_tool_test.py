import os
from contextlib import contextmanager
from approvaltests import Options, verify
from approvaltests.scrubbers import combine_scrubbers

from modernizer.tools.tool_library import ToolLibrary
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

def verifyEditTool(framework, setup_file, setup_content, command, expected_content, tmp_path=None):
    """
    Verify an edit tool command and check the modified file's content.
    
    Args:
        framework: The tool framework to execute the command
        setup_file: The filename to create and edit
        setup_content: The initial content of the file
        command: The edit command to execute
        expected_content: The expected content after editing
        tmp_path: Optional temporary path to change to during execution
    """
    # Create scrubber for consistent output
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
        cmd, result = framework.parse_and_execute(command)
        
        # Verify the file was modified correctly
        if os.path.exists(setup_file):
            with open(setup_file, "r") as f:
                actual_content = f.read()
                final_file_info = f"File after edit: {setup_file}\nFinal content:\n--- FINAL CONTENT START ---\n{actual_content}\n--- FINAL CONTENT END ---"
        else:
            final_file_info = "File not found after edit"
            
        # Create verification output including both initial and final file content
        verify(f"Command:\n{cmd}\n\nResult:\n{result}\n\n{initial_file_info}\n\n{final_file_info}", options=Options().with_scrubber(multi_scrubber))
    
    if tmp_path:
        with temp_directory(tmp_path):
            _execute_and_verify()
    else:
        _execute_and_verify()

def test_edit_file_replace_single_character(tmp_path):
    verifyEditTool(library, "test.txt", "a", "/edit-file test.txt 1 1 b", "b", tmp_path=tmp_path)

def test_edit_file_replace_single_word(tmp_path):
    verifyEditTool(library, "test.txt", "old", "/edit-file test.txt 1 1 new", "new", tmp_path=tmp_path)

def test_edit_file_replace_two_consecutive_lines_with_one(tmp_path):
    verifyEditTool(library, "test.txt", "line1\nline2\nline3", "/edit-file test.txt 2 3 newline", "line1\nnewline\n", tmp_path=tmp_path)