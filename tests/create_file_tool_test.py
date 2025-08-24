from approvaltests import Options, verify

from tools.tool_library import ToolLibrary
from .test_helpers import all_scrubbers, temp_directory

library = ToolLibrary()


def verify_create_tool(library, command, expected_filename, tmp_path):
    with temp_directory(tmp_path):
        tool = library.parse_tool(command)
        result = library.execute_parsed_tool(tool)

        with open(expected_filename, "r") as f:
                actual_content = f.read()
                file_info = f"File created: {expected_filename}\nFile content:\n--- FILE CONTENT START ---\n{actual_content}\n--- FILE CONTENT END ---"

        verify(
            f"Command:\n{command}\n\nResult:\n{result}\n\n{file_info}",
            options=Options().with_scrubber(all_scrubbers())
        )


def test_create_tool_single_character_name(tmp_path):
    verify_create_tool(library, "/create-file a", "a", tmp_path=tmp_path)


def test_create_tool_simple_name_with_extension(tmp_path):
    verify_create_tool(library, "/create-file test.txt", "test.txt", tmp_path=tmp_path)


def test_create_tool_single_character_content(tmp_path):
    verify_create_tool(library, "/create-file test.txt a", "test.txt", tmp_path=tmp_path)


def test_create_tool_simple_text_content(tmp_path):
    verify_create_tool(library, "/create-file readme.txt Hello World", "readme.txt", tmp_path=tmp_path)


def test_create_tool_newline_content(tmp_path):
    verify_create_tool(library, '/create-file multi.txt "Line 1\\nLine 2"', "multi.txt", tmp_path=tmp_path)


def test_create_tool_json_content(tmp_path):
    verify_create_tool(library, '/create-file config.json {"name": "test"}', "config.json", tmp_path=tmp_path)


def test_create_tool_explicit_empty_content(tmp_path):
    verify_create_tool(library, '/create-file empty.txt ""', "empty.txt", tmp_path=tmp_path)


def test_create_file_in_nonexistent_directory(tmp_path):
    verify_create_tool(library, f'/create-file src/utils/helper.py "# Helper module"', "src/utils/helper.py",
                       tmp_path=tmp_path)


def test_create_file_already_exists(tmp_path):
    with temp_directory(tmp_path):
        tool = library.parse_tool("/create-file existing.txt")
        library.execute_parsed_tool(tool)

        tool = library.parse_tool("/create-file existing.txt")
        result = library.execute_parsed_tool(tool)
        assert 'already exists' in result.lower() or 'exists' in result.lower()
