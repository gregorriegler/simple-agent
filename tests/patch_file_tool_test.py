import os
from approvaltests import Options, verify

from simple_agent.tools.tool_library import ToolLibrary
from .test_helpers import all_scrubbers, temp_directory

library = ToolLibrary()


def test_patch_file_simple_replacement(tmp_path):
    initial_content = "line1\nold line\nline3"
    patch_content = "@@ -2,1 +2,1 @@\n-old line\n+new line"
    command = f'🛠️ patch-file test.txt "{patch_content}"'
    verify_patch_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_patch_file_add_line(tmp_path):
    initial_content = "line1\nline2"
    patch_content = "@@ -1,2 +1,3 @@\n line1\n+added line\n line2"
    command = f'🛠️ patch-file test.txt "{patch_content}"'
    verify_patch_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_patch_file_delete_line(tmp_path):
    initial_content = "line1\ndelete me\nline3"
    patch_content = "@@ -1,3 +1,2 @@\n line1\n-delete me\n line3"
    command = f'🛠️ patch-file test.txt "{patch_content}"'
    verify_patch_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_patch_file_multiple_changes(tmp_path):
    initial_content = "line1\nold line\nkeep this\ndelete me\nline5"
    patch_content = "@@ -1,5 +1,4 @@\n line1\n-old line\n+new line\n keep this\n-delete me\n line5"
    command = f'🛠️ patch-file test.txt "{patch_content}"'
    verify_patch_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_patch_file_python_code(tmp_path):
    initial_content = """def hello():
    old_var = 1
    return old_var"""
    patch_content = "@@ -2,1 +2,1 @@\n-    old_var = 1\n+    new_var = 2"
    command = f'🛠️ patch-file test.py "{patch_content}"'
    verify_patch_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)


def test_patch_file_context_mismatch_error(tmp_path):
    initial_content = "line1\nactual line\nline3"
    patch_content = "@@ -2,1 +2,1 @@\n-expected line\n+new line"
    command = f'🛠️ patch-file test.txt "{patch_content}"'
    verify_patch_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_patch_file_nonexistent_file(tmp_path):
    patch_content = "@@ -1,1 +1,1 @@\n-old\n+new"
    command = f'🛠️ patch-file nonexistent.txt "{patch_content}"'
    verify_patch_tool(library, "nonexistent.txt", None, command, tmp_path=tmp_path)


def test_patch_file_empty_patch(tmp_path):
    initial_content = "line1\nline2"
    command = '🛠️ patch-file test.txt ""'
    verify_patch_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_patch_file_invalid_patch_header(tmp_path):
    initial_content = "line1\nline2"
    patch_content = "invalid patch format\n-old\n+new"
    command = f'🛠️ patch-file test.txt "{patch_content}"'
    verify_patch_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_patch_file_with_spaces_in_filename(tmp_path):
    initial_content = "original content"
    patch_content = "@@ -1,1 +1,1 @@\n-original content\n+updated content"
    command = f'🛠️ patch-file "notes folder/note file.txt" "{patch_content}"'
    verify_patch_tool(library, "notes folder/note file.txt", initial_content, command, tmp_path=tmp_path)


def verify_patch_tool(library, setup_file, setup_content, command, tmp_path):
    with temp_directory(tmp_path):
        if setup_content is not None:
            os.makedirs(os.path.dirname(setup_file) or '.', exist_ok=True)
            with open(setup_file, "w", encoding='utf-8') as f:
                f.write(setup_content)
            initial_file_info = f"Initial file: {setup_file}\nInitial content:\n--- INITIAL CONTENT START ---\n{setup_content}\n--- INITIAL CONTENT END ---"
        else:
            initial_file_info = f"Initial file: {setup_file} (does not exist)"

        tool = library.parse_tool(command)
        result = library.execute_parsed_tool(tool)

        if os.path.exists(setup_file):
            with open(setup_file, "r", encoding='utf-8') as f:
                actual_content = f.read()
            final_file_info = f"File after patch: {setup_file}\nFinal content:\n--- FINAL CONTENT START ---\n{actual_content}\n--- FINAL CONTENT END ---"
        else:
            final_file_info = f"File after patch: {setup_file} (still does not exist)"

        verify(
            f"Command:\n{command}\n\nResult:\n{result}\n\n{initial_file_info}\n\n{final_file_info}",
            options=Options().with_scrubber(all_scrubbers())
        )
