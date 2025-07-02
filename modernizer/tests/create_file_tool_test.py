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

def verifyCreateTool(framework, command, expected_filename, expected_content=None, tmp_path=None):
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
        expected_content = ""
    
    # Create scrubber for consistent output
    path_scrubber = create_path_scrubber()
    date_scrubber = create_date_scrubber()
    ls_error_scrubber = create_ls_error_scrubber()
    multi_scrubber = combine_scrubbers(path_scrubber, date_scrubber, ls_error_scrubber)
    
    def _execute_and_verify():
        cmd, result = framework.parse_and_execute(command)
        
        # Check if file was created
        if not os.path.exists(expected_filename):
            raise AssertionError(f"File '{expected_filename}' should have been created")
        
        # Read and verify file content
        with open(expected_filename, "r") as f:
            actual_content = f.read()
        
        if actual_content != expected_content:
            raise AssertionError(f"File '{expected_filename}' should contain '{expected_content}', but contains '{actual_content}'")
        
        # Create verification output including file content
        file_info = f"File created: {expected_filename}\nFile content:\n--- FILE CONTENT START ---\n{actual_content}\n--- FILE CONTENT END ---"
        verify(f"Command:\n{cmd}\n\nResult:\n{result}\n\n{file_info}", options=Options().with_scrubber(multi_scrubber))
    
    if tmp_path:
        with temp_directory(tmp_path):
            _execute_and_verify()
    else:
        _execute_and_verify()

def test_create_tool_single_character_name(tmp_path):
    verifyCreateTool(library, "/create-file a", "a", tmp_path=tmp_path)

def test_create_tool_simple_name_with_extension(tmp_path):
    verifyCreateTool(library, "/create-file test.txt", "test.txt", tmp_path=tmp_path)

def test_create_tool_single_character_content(tmp_path):
    verifyCreateTool(library, "/create-file test.txt a", "test.txt", "a", tmp_path=tmp_path)

def test_create_tool_simple_text_content(tmp_path):
    verifyCreateTool(library, "/create-file readme.txt Hello World", "readme.txt", "Hello World", tmp_path=tmp_path)

def test_create_tool_newline_content(tmp_path):
    verifyCreateTool(library, '/create-file multi.txt "Line 1\\nLine 2"', "multi.txt", "Line 1\nLine 2", tmp_path=tmp_path)

def test_create_tool_json_content(tmp_path):
    verifyCreateTool(library, '/create-file config.json {"name": "test"}', "config.json", '{"name": "test"}', tmp_path=tmp_path)

def test_create_tool_explicit_empty_content(tmp_path):
    verifyCreateTool(library, '/create-file empty.txt ""', "empty.txt", "", tmp_path=tmp_path)

def test_create_file_in_nonexistent_directory(tmp_path):
    verifyCreateTool(library, f'/create-file src/utils/helper.py "# Helper module"', "src/utils/helper.py", "# Helper module", tmp_path=tmp_path)

def test_create_file_permission_error():
    """Test creating file in system directory without permissions should return error message"""
    # Use a path that should definitely cause permission error on Windows
    cmd, result = library.parse_and_execute("/create-file C:/Windows/System32/test.txt")
    
    # Should fail with permission error - result is a string containing the error
    assert 'permission' in result.lower() or 'denied' in result.lower() or 'error' in result.lower()

def test_create_file_already_exists(tmp_path):
    """Test creating file that already exists should return error message"""
    with temp_directory(tmp_path):
        # First create a file
        library.parse_and_execute("/create-file existing.txt")
        
        # Try to create the same file again
        cmd, result = library.parse_and_execute("/create-file existing.txt")
        
        # Should fail with "file already exists" error
        assert 'already exists' in result.lower() or 'exists' in result.lower()

def test_create_file_invalid_filename():
    """Test creating file with invalid characters should return error message"""
    cmd, result = library.parse_and_execute('/create-file "file<>name.txt"')
    
    # Should fail with invalid filename error
    assert 'invalid' in result.lower() or 'error' in result.lower()