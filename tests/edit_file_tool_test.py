from approvaltests import Options, verify

from tools.tool_library import ToolLibrary
from .test_helpers import all_scrubbers, temp_directory

library = ToolLibrary()


def test_edit_file_replace_single_character(tmp_path):
    verify_edit_tool(library, "test.txt", "a", "🛠️ edit-file test.txt replace 1 b", tmp_path=tmp_path)


def test_edit_file_replace_single_word(tmp_path):
    verify_edit_tool(library, "test.txt", "old", "🛠️ edit-file test.txt replace 1-1 new", tmp_path=tmp_path)


def test_edit_file_replace_two_consecutive_lines_with_one(tmp_path):
    verify_edit_tool(library, "test.txt", "line1\nline2\nline3", "🛠️ edit-file test.txt replace 2-3 newline", tmp_path=tmp_path)


def test_edit_file_replace_two_consecutive_lines_with_two(tmp_path):
    command = "🛠️ edit-file test.txt replace 2-3 newline1\nnewline2"
    verify_edit_tool(library, "test.txt", "line1\nline2\nline3", command, tmp_path=tmp_path)


def test_edit_file_replace_two_consecutive_lines_with_four(tmp_path):
    command = "🛠️ edit-file test.txt replace 2-3 newline1\nnewline2\nnewline3\nnewline4"
    verify_edit_tool(library, "test.txt", "line1\nline2\nline3", command, tmp_path=tmp_path)


def test_edit_file_replace_a_lines_with_lines_in_quotes(tmp_path):
    command = "🛠️ edit-file test.txt replace 2 \"insert1\ninsert2\""
    verify_edit_tool(library, "test.txt", "line1\nline2", command, tmp_path=tmp_path)


def test_edit_file_replace_empty_lines_with_function(tmp_path):
    initial_content = "line1\nline2\n\n\n\nline6"
    function_def = "def hello():\n    return 'world'"
    command = f"🛠️ edit-file template.py replace 3-5 {function_def}"
    verify_edit_tool(library, "template.py", initial_content, command, tmp_path=tmp_path)


def test_edit_file_insert_two_lines_to_empty_file(tmp_path):
    command = "🛠️ edit-file empty.txt insert 1 line1\nline2"
    verify_edit_tool(library, "empty.txt", "", command, tmp_path=tmp_path)


def test_edit_file_insert_three_lines_to_empty_file(tmp_path):
    command = "🛠️ edit-file empty.txt insert 1 line1\nline2\nline3"
    verify_edit_tool(library, "empty.txt", "", command, tmp_path=tmp_path)


def test_edit_file_insert_a_line_between_two_lines(tmp_path):
    initial_content = "line1\nline2"
    command = "🛠️ edit-file test.txt insert 2 line1.5\n"
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_insert_line_without_explicit_newline_adds_newline_automatically(tmp_path):
    initial_content = "line1\nline2"
    command = "🛠️ edit-file test.txt insert 2 inserted_line"
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_delete_a_line(tmp_path):
    initial_content = "line1\nline2"
    command = "🛠️ edit-file test.txt delete 1"
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def verify_edit_tool(library, setup_file, setup_content, command, tmp_path):
    with temp_directory(tmp_path):
        with open(setup_file, "w", encoding='utf-8') as f:
            f.write(setup_content)

        initial_file_info = f"Initial file: {setup_file}\nInitial content:\n--- INITIAL CONTENT START ---\n{setup_content}\n--- INITIAL CONTENT END ---"

        tool = library.parse_tool(command)
        result = library.execute_parsed_tool(tool)

        with open(setup_file, "r", encoding='utf-8') as f:
            actual_content = f.read()

        final_file_info = f"File after edit: {setup_file}\nFinal content:\n--- FINAL CONTENT START ---\n{actual_content}\n--- FINAL CONTENT END ---"

        verify(
            f"Command:\n{command}\n\nResult:\n{result}\n\n{initial_file_info}\n\n{final_file_info}",
            options=Options().with_scrubber(all_scrubbers())
        )
