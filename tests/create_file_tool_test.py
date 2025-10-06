from approvaltests import Options, verify

from simple_agent.tools.tool_library import ToolLibrary
from .test_helpers import all_scrubbers, temp_directory

library = ToolLibrary()


def test_create_tool_single_character_name(tmp_path):
    verify_create_tool(library, "🛠️ create-file a", "a", tmp_path=tmp_path)


def test_create_tool_simple_name_with_extension(tmp_path):
    verify_create_tool(library, "🛠️ create-file test.txt", "test.txt", tmp_path=tmp_path)


def test_create_tool_single_character_content(tmp_path):
    verify_create_tool(library, "🛠️ create-file test.txt a", "test.txt", tmp_path=tmp_path)


def test_create_tool_simple_text_content(tmp_path):
    verify_create_tool(library, "🛠️ create-file readme.txt Hello World", "readme.txt", tmp_path=tmp_path)


def test_create_tool_newline_content(tmp_path):
    verify_create_tool(library, '🛠️ create-file multi.txt "Line 1\\nLine 2"', "multi.txt", tmp_path=tmp_path)


def test_create_tool_json_content(tmp_path):
    verify_create_tool(library, '🛠️ create-file config.json {"name": "test"}', "config.json", tmp_path=tmp_path)


def test_create_tool_filename_with_spaces(tmp_path):
    verify_create_tool(library, '🛠️ create-file "notes folder/note file.txt" "First line\\nSecond line"',
                      "notes folder/note file.txt", tmp_path=tmp_path)


def test_create_tool_content_with_leading_and_trailing_spaces(tmp_path):
    verify_create_tool(library, '🛠️ create-file padded.txt "  spaced content  "', "padded.txt", tmp_path=tmp_path)


def test_create_tool_explicit_empty_content(tmp_path):
    verify_create_tool(library, '🛠️ create-file empty.txt ""', "empty.txt", tmp_path=tmp_path)


def test_create_file_in_nonexistent_directory(tmp_path):
    verify_create_tool(library, f'🛠️ create-file src/utils/helper.py "# Helper module"', "src/utils/helper.py",
                       tmp_path=tmp_path)


def test_create_file_already_exists(tmp_path):
    with temp_directory(tmp_path):
        tool = library.parse_tool("🛠️ create-file existing.txt")
        library.execute_parsed_tool(tool)

        tool = library.parse_tool("🛠️ create-file existing.txt")
        result = library.execute_parsed_tool(tool)
        assert 'already exists' in result.feedback.lower() or 'exists' in result.feedback.lower()


def test_create_tool_on_second_line(tmp_path):
    verify_create_tool(library, "let me create a file\n🛠️ create-file a", "a", tmp_path=tmp_path)


def test_create_tool_on_second_line_with_multiline_content(tmp_path):
    verify_create_tool(library, "let me create a file\n🛠️ create-file test.txt Line1\nLine2", "test.txt", tmp_path=tmp_path)


def test_create_tool_stops_at_next_command(tmp_path):
    verify_create_tool(library, "🛠️ create-file test.txt Line1\nLine2\n🛠️ ls", "test.txt", tmp_path=tmp_path)


def test_create_tool_content_with_single_quotes(tmp_path):
    verify_create_tool(library, '🛠️ create-file test.txt \'He said "Hello"\'', "test.txt", tmp_path=tmp_path)


def test_create_tool_json_with_nested_quotes(tmp_path):
    verify_create_tool(library, '🛠️ create-file config.json \'{"name": "John", "message": "Hello \\"World\\""}\'', "config.json", tmp_path=tmp_path)


def test_create_tool_content_with_backslashes(tmp_path):
    verify_create_tool(library, '🛠️ create-file paths.txt "Path: C:\\\\Users\\\\test"', "paths.txt", tmp_path=tmp_path)


def test_create_tool_content_with_tabs(tmp_path):
    verify_create_tool(library, '🛠️ create-file table.txt "Column1\\tColumn2\\tColumn3"', "table.txt", tmp_path=tmp_path)


def test_create_tool_content_with_mixed_special_characters(tmp_path):
    verify_create_tool(library, '🛠️ create-file special.txt "Special: @#$%^&*()_+-={}[]|\\\\:;\'<>?,./"', "special.txt", tmp_path=tmp_path)


def test_create_tool_content_with_unicode_characters(tmp_path):
    verify_create_tool(library, '🛠️ create-file unicode.txt "Unicode: 🚀 café naïve résumé"', "unicode.txt", tmp_path=tmp_path)


def test_create_tool_content_with_single_quotes_inside_double_quotes(tmp_path):
    verify_create_tool(library, '🛠️ create-file test.txt "It\'s a test"', "test.txt", tmp_path=tmp_path)


def test_create_tool_multi_line_content(tmp_path):
    verify_create_tool(library,
"""
🛠️ create-file a First Line
Second Line
Third Line
""", "a", tmp_path=tmp_path)


def verify_create_tool(library, command, expected_filename, tmp_path):
    with temp_directory(tmp_path):
        tool = library.parse_tool(command)
        result = library.execute_parsed_tool(tool)

        with open(expected_filename, "r", encoding='utf-8') as f:
            actual_content = f.read()
            file_info = f"File created: {expected_filename}\nFile content:\n--- FILE CONTENT START ---\n{actual_content}\n--- FILE CONTENT END ---"

        verify(
            f"Command:\n{command}\n\nResult:\n{result}\n\n{file_info}",
            options=Options().with_scrubber(all_scrubbers())
        )
