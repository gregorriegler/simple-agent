import os
from approvaltests import Options, verify

from tests.test_helpers import all_scrubbers, temp_directory, create_all_tools_for_test

library = create_all_tools_for_test()


def test_edit_file_replace_single_word(tmp_path):
    initial_content = "old\n"
    command = """🛠️[edit-file test.txt delete_lines_then_insert 1-1]
new
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_single_word_without_newlines(tmp_path):
    initial_content = "old"
    command = """🛠️[edit-file test.txt delete_lines_then_insert 1-1]
new
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_two_consecutive_lines_with_one(tmp_path):
    initial_content = "line1\nline2\nline3\n"
    command = """🛠️[edit-file test.txt delete_lines_then_insert 2-3]
newline
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_a_lines_with_lines_in_quotes(tmp_path):
    initial_content = "line1\nline2\n"
    command = """🛠️[edit-file test.txt delete_lines_then_insert 2]
"insert1
insert2"
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_empty_lines_with_function(tmp_path):
    initial_content = "line1\nline2\n\n\n\nline6\n"
    command = """🛠️[edit-file template.py delete_lines_then_insert 3-5]
def hello():
    return 'world'
🛠️[/end]"""
    verify_edit_tool(library, "template.py", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_path_with_spaces(tmp_path):
    initial_content = "original line\n"
    command = """🛠️[edit-file "notes folder/note file.txt" delete_lines_then_insert 1]
"updated line"
🛠️[/end]"""
    verify_edit_tool(library, "notes folder/note file.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_insert_three_lines_to_empty_file(tmp_path):
    initial_content = ""
    command = """🛠️[edit-file empty.txt insert 1]
line1
line2
line3
🛠️[/end]"""
    verify_edit_tool(library, "empty.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_insert_line_without_explicit_newline_adds_newline_automatically(tmp_path):
    initial_content = "line1\nline2\n"
    command = """🛠️[edit-file test.txt insert 2]
inserted_line
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_insert_multiline_without_trailing_newline_adds_newline_automatically(tmp_path):
    initial_content = "line1\nline2\n"
    command = """🛠️[edit-file test.txt insert 2]
inserted_line1
inserted_line2
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_preserves_indentation_in_multiline_content(tmp_path):
    initial_content = "line1\nline2\n"
    command = """🛠️[edit-file test.py insert 3]
def hello():
    return 'world'
🛠️[/end]"""
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)


def test_edit_file_insert_beyond_last_line_appends_to_end(tmp_path):
    initial_content = "line1\nline2\n"
    command = """🛠️[edit-file test.txt insert 3]
line3
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_insert_far_beyond_last_line_appends_to_end_and_pads_with_empty_lines(tmp_path):
    initial_content = "line1\nline2\n"
    command = """🛠️[edit-file test.txt insert 10]
line10
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_insert_without_content_inserts_an_empty_line(tmp_path):
    initial_content = "line1\nline2\n"
    command = """🛠️[edit-file test.txt insert 2]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_delete_a_line(tmp_path):
    initial_content = "line1\nline2\n"
    command = """🛠️[edit-file test.txt delete 1]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_delete_range_extending_past_file_end(tmp_path):
    initial_content = "line1\nline2\nline3\n"
    command = """🛠️[edit-file test.txt delete 2-10]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_range_beyond_file_end_leaves_file_unchanged(tmp_path):
    initial_content = "line1\nline2\n"
    command = """🛠️[edit-file test.txt delete_lines_then_insert 5-7]
replacement
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_with_auto_indent_python(tmp_path):
    initial_content = "line1\n    existing = 1\nline3\n"
    command = """🛠️[edit-file test.py delete_lines_then_insert 2]
new = 2
🛠️[/end]"""
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)


def test_edit_file_insert_with_auto_indent(tmp_path):
    initial_content = "line1\n    line2\nline3\n"
    command = """🛠️[edit-file test.py insert 2]
new_line
🛠️[/end]"""
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_preserves_manual_indentation(tmp_path):
    initial_content = "line1\n    existing\nline3\n"
    command = """🛠️[edit-file test.py delete_lines_then_insert 2]
        manually_indented
🛠️[/end]"""
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_multiline_only_indents_first_line(tmp_path):
    initial_content = "line1\n    existing\nline3\n"
    command = """🛠️[edit-file test.py delete_lines_then_insert 2]
line1
line2
    line3
🛠️[/end]"""
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)


def test_edit_file_replace_complex_python_program_rename_functions_and_variables(tmp_path):
    initial_content = """class DataProcessor:
    def __init__(self, input_data):
        self.raw_data = input_data
        self.processed_items = []

    def validate_input(self, data_item):
        if not data_item:
            return False
        return len(data_item) > 0

    def process_single_item(self, item):
        if self.validate_input(item):
            cleaned_item = item.strip().lower()
            return cleaned_item
        return None

    def batch_process(self):
        for current_item in self.raw_data:
            result = self.process_single_item(current_item)
            if result:
                self.processed_items.append(result)
        return self.processed_items
"""

    replacement_content = """class DataHandler:
    def __init__(self, source_data):
        self.original_data = source_data
        self.cleaned_items = []

    def check_validity(self, data_entry):
        if not data_entry:
            return False
        return len(data_entry) > 0

    def handle_single_entry(self, entry):
        if self.check_validity(entry):
            normalized_entry = entry.strip().lower()
            return normalized_entry
        return None

    def process_all(self):
        for current_entry in self.original_data:
            outcome = self.handle_single_entry(current_entry)
            if outcome:
                self.cleaned_items.append(outcome)
        return self.cleaned_items
"""

    command = f"""🛠️[edit-file complex_program.py delete_lines_then_insert 1-20]
{replacement_content}
🛠️[/end]"""
    verify_edit_tool(library, "complex_program.py", initial_content, command, tmp_path=tmp_path)


def test_edit_file_string_replace_basic(tmp_path):
    """Basic string replacement - find and replace exact match."""
    initial_content = "hello world\n"
    command = """🛠️[edit-file test.txt string_replace]
<<<<<<< OLD
hello
=======
goodbye
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_string_replace_multiline(tmp_path):
    """Replace multiple lines at once."""
    initial_content = "line1\nline2\nline3\nline4\n"
    command = """🛠️[edit-file test.txt string_replace]
<<<<<<< OLD
line2
line3
=======
replaced
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_string_replace_preserves_indentation(tmp_path):
    """Whitespace in old_string and new_string is preserved exactly."""
    initial_content = "def foo():\n    old_code = 1\n    return old_code\n"
    command = """🛠️[edit-file test.py string_replace]
<<<<<<< OLD
    old_code = 1
=======
    new_code = 42
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)


def test_edit_file_string_replace_not_found(tmp_path):
    """Error when string is not found in file."""
    initial_content = "hello world\n"
    command = """🛠️[edit-file test.txt string_replace]
<<<<<<< OLD
nonexistent
=======
replacement
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_string_replace_multiple_matches_error(tmp_path):
    """Error when string appears multiple times - need more context."""
    initial_content = "foo\nbar\nfoo\nbaz\n"
    command = """🛠️[edit-file test.txt string_replace]
<<<<<<< OLD
foo
=======
replaced
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_string_replace_with_unique_context(tmp_path):
    """Adding surrounding context makes the match unique."""
    initial_content = "foo\nbar\nfoo\nbaz\n"
    command = """🛠️[edit-file test.txt string_replace]
<<<<<<< OLD
bar
foo
=======
bar
replaced
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_string_replace_delete_string(tmp_path):
    """Empty new_string effectively deletes the old_string."""
    initial_content = "keep\ndelete_me\nkeep\n"
    command = """🛠️[edit-file test.txt string_replace]
<<<<<<< OLD
delete_me
=======
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


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

def test_edit_file_string_replace_all(tmp_path):
    """Replace all occurrences of a string."""
    initial_content = "foo\nbar\nfoo\nbaz\n"
    command = """🛠️[edit-file test.txt string_replace all]
<<<<<<< OLD
foo
=======
replaced
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_string_replace_nth(tmp_path):
    """Replace the nth occurrence of a string."""
    initial_content = "foo\nbar\nfoo\nbaz\n"
    command = """🛠️[edit-file test.txt string_replace nth:2]
<<<<<<< OLD
foo
=======
replaced
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)


def test_edit_file_string_replace_single_default(tmp_path):
    """Replace a single occurrence of a string by default."""
    initial_content = "foo\nbar\nbaz\n"
    command = """🛠️[edit-file test.txt string_replace]
<<<<<<< OLD
foo
=======
replaced
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)

def test_string_replace_with_extra_args(tmp_path):
    """Should raise an error if too many arguments are provided."""
    initial_content = "foo\nbar\nfoo\nbaz\n"
    command = """🛠️[edit-file test.txt string_replace all extra_arg]
<<<<<<< OLD
foo
=======
replaced
>>>>>>> NEW
🛠️[/end]"""
    verify_edit_tool(library, "test.txt", initial_content, command, tmp_path=tmp_path)
