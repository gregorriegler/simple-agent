import os
import textwrap
from approvaltests import Options, verify

from tests.test_helpers import all_scrubbers, temp_directory, create_all_tools_for_test

library = create_all_tools_for_test()


def verify_edit_tool(library, setup_file, setup_content, command, tmp_path):
    with temp_directory(tmp_path):
        os.makedirs(os.path.dirname(setup_file) or '.', exist_ok=True)
        with open(setup_file, "w", encoding='utf-8') as f:
            f.write(setup_content)

        initial_file_info = f"Initial file: {setup_file}\nInitial content:\n--- INITIAL CONTENT START ---\n{setup_content}\n--- INITIAL CONTENT END ---"

        tool = library.parse_message_and_tools(command)
        result = library.execute_parsed_tool(tool.tools[0])
        with open(setup_file, "r", encoding='utf-8') as f:
            actual_content = f.read()
        final_file_info = f"File after edit: {setup_file}\nFinal content:\n--- FINAL CONTENT START ---\n{actual_content}\n--- FINAL CONTENT END ---"
        verify(
            f"Command:\n{command}\n\nResult:\n{result}\n\n{initial_file_info}\n\n{final_file_info}",
            options=Options().with_scrubber(all_scrubbers())
        )


def test_replace_file_content_basic(tmp_path):
    """Basic string replacement - find and replace exact match."""
    initial_content = "hello world\n"
    command = textwrap.dedent("""
        🛠️[replace-file-content test.txt single]
        hello
        @@@
        goodbye
        🛠️[/end]
        """).strip()
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_replace_file_content_multiline(tmp_path):
    """Replace multiple lines at once."""
    initial_content = "line1\nline2\nline3\nline4\n"
    command = textwrap.dedent("""
        🛠️[replace-file-content test.txt single]
        line2
        line3
        @@@
        replaced
        🛠️[/end]
        """).strip()
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_replace_file_content_preserves_indentation(tmp_path):
    """Whitespace in old_string and new_string is preserved exactly."""
    initial_content = "def foo():\n    old_code = 1\n    return old_code\n"
    command = textwrap.dedent("""
        🛠️[replace-file-content test.py single]
            old_code = 1
        @@@
            new_code = 42
        🛠️[/end]
        """).strip()
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)


def test_replace_file_content_not_found(tmp_path):
    """Error when string is not found in file."""
    initial_content = "hello world\n"
    command = textwrap.dedent("""
        🛠️[replace-file-content test.txt single]
        nonexistent
        @@@
        replacement
        🛠️[/end]
        """).strip()
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_replace_file_content_multiple_matches_error(tmp_path):
    """When string appears multiple times, single mode replaces only the first occurrence."""
    initial_content = "foo\nbar\nfoo\nbaz\n"
    command = textwrap.dedent("""
        🛠️[replace-file-content test.txt single]
        foo
        @@@
        replaced
        🛠️[/end]
        """).strip()
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_replace_file_content_with_unique_context(tmp_path):
    """Adding surrounding context makes the match unique."""
    initial_content = "foo\nbar\nfoo\nbaz\n"
    command = textwrap.dedent("""
        🛠️[replace-file-content test.txt single]
        bar
        foo
        @@@
        bar
        replaced
        🛠️[/end]
        """).strip()
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_replace_file_content_delete_string(tmp_path):
    """Empty new_string effectively deletes the old_string."""
    initial_content = "keep\ndelete_me\nkeep\n"
    command = textwrap.dedent("""
        🛠️[replace-file-content test.txt single]
        delete_me
        @@@
        🛠️[/end]
        """).strip()
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_replace_file_content_all(tmp_path):
    """Replace all occurrences of a string."""
    initial_content = "foo\nbar\nfoo\nbaz\n"
    command = textwrap.dedent("""
        🛠️[replace-file-content test.txt all]
        foo
        @@@
        replaced
        🛠️[/end]
        """).strip()
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)

def test_replace_file_content_single_default(tmp_path):
    """Replace a single occurrence of a string by default."""
    initial_content = "foo\nbar\nbaz\n"
    command = textwrap.dedent("""
        🛠️[replace-file-content test.txt single]
        foo
        @@@
        replaced
        🛠️[/end]
        """).strip()
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)
