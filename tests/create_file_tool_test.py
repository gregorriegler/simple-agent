from approvaltests import Options, verify

from simple_agent.tools.all_tools import AllTools
from .test_helpers import all_scrubbers, temp_directory

library = AllTools()


def test_create_tool_single_character_name(tmp_path):
    verify_create_tool(library, "🛠️ create-file a", "a", tmp_path=tmp_path)


def test_create_tool_simple_name_with_extension(tmp_path):
    verify_create_tool(library, "🛠️ create-file test.txt", "test.txt", tmp_path=tmp_path)


def test_create_tool_single_character_content(tmp_path):
    verify_create_tool(library, "🛠️ create-file test.txt a", "test.txt", tmp_path=tmp_path)


def test_create_tool_simple_text_content(tmp_path):
    verify_create_tool(library, "🛠️ create-file readme.txt Hello World", "readme.txt", tmp_path=tmp_path)


def test_create_tool_json_content(tmp_path):
    verify_create_tool(library, '🛠️ create-file config.json {"name": "test"}', "config.json", tmp_path=tmp_path)


def test_create_file_in_nonexistent_directory(tmp_path):
    verify_create_tool(library, f'🛠️ create-file src/utils/helper.py # Helper module', "src/utils/helper.py",
                       tmp_path=tmp_path)


def test_create_file_already_exists(tmp_path):
    with temp_directory(tmp_path):
        tool = library.parse_message_and_tools("🛠️ create-file existing.txt")
        library.execute_parsed_tool(tool.tools[0])

        tool = library.parse_message_and_tools("🛠️ create-file existing.txt")
        result = library.execute_parsed_tool(tool.tools[0])
        assert 'already exists' in result.feedback.lower() or 'exists' in result.feedback.lower()


def test_create_tool_on_second_line(tmp_path):
    verify_create_tool(library, "let me create a file\n🛠️ create-file a", "a", tmp_path=tmp_path)


def test_create_tool_on_second_line_with_multiline_content(tmp_path):
    verify_create_tool(library, "let me create a file\n🛠️ create-file test.txt Line1\nLine2", "test.txt", tmp_path=tmp_path)


def test_create_tool_stops_at_next_command(tmp_path):
    verify_create_tool(library, "🛠️ create-file test.txt Line1\nLine2\n🛠️ ls", "test.txt", tmp_path=tmp_path)




def test_create_tool_multi_line_content(tmp_path):
    verify_create_tool(library,
"""
🛠️ create-file a First Line
Second Line
Third Line
""", "a", tmp_path=tmp_path)


def verify_create_tool(library, command, expected_filename, tmp_path):
    with temp_directory(tmp_path):
        tool = library.parse_message_and_tools(command)
        result = library.execute_parsed_tool(tool.tools[0])

        with open(expected_filename, "r", encoding='utf-8') as f:
            actual_content = f.read()
            file_info = f"File created: {expected_filename}\nFile content:\n--- FILE CONTENT START ---\n{actual_content}\n--- FILE CONTENT END ---"

        verify(
            f"Command:\n{command}\n\nResult:\n{result}\n\n{file_info}",
            options=Options().with_scrubber(all_scrubbers())
        )
