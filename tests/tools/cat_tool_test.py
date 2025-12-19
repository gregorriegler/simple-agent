import pytest

from tests.test_helpers import create_all_tools_for_test, create_temp_file, verify_tool

library = create_all_tools_for_test()
pytestmark = pytest.mark.asyncio

async def test_cat_tool_single_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "Hello world\nSecond line\nThird line")

    await verify_tool(library, f"🛠️[cat {temp_file} /]")

async def test_cat_tool_nonexistent_file():
    await verify_tool(library, "🛠️[cat /nonexistent/file.txt /]")

async def test_cat_tool_empty_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "empty.txt", "")

    await verify_tool(library, f"🛠️[cat {temp_file} /]")

async def test_cat_tool_empty_file_with_range(tmp_path):
    temp_file = create_temp_file(tmp_path, "empty.txt", "")

    await verify_tool(library, f"🛠️[cat {temp_file} 1-5 /]")

async def test_cat_tool_with_special_characters(tmp_path):
    special_file = create_temp_file(tmp_path, "special-file_name.txt", "Content with special chars: !@#$%^&*()")

    await verify_tool(library, f"🛠️[cat {special_file} /]")

async def test_cat_tool_single_line_from_beginning(tmp_path):
    temp_file = create_temp_file(tmp_path, "single_line_test.txt", "first line content\nsecond line\nthird line")

    await verify_tool(library, f"🛠️[cat {temp_file} 1-1 /]")

async def test_cat_tool_multiple_lines_from_beginning(tmp_path):
    temp_file = create_temp_file(tmp_path, "multiple_lines_test.txt", "first line content\nsecond line\nthird line\nfourth line")

    await verify_tool(library, f"🛠️[cat {temp_file} 1-3 /]")

async def test_cat_tool_specific_line_range(tmp_path):
    content = "\n".join([f"Line {i} content" for i in range(1, 16)])
    temp_file = create_temp_file(tmp_path, "range_test.txt", content)

    await verify_tool(library, f"🛠️[cat {temp_file} 5-10 /]")

async def test_cat_tool_invalid_range_format(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "line 1\nline 2\nline 3")

    await verify_tool(library, f"🛠️[cat {temp_file} abc-def /]")

async def test_cat_tool_reversed_range(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "line 1\nline 2\nline 3")

    await verify_tool(library, f"🛠️[cat {temp_file} 10-5 /]")

async def test_cat_tool_range_beyond_file_length(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "line 1\nline 2\nline 3")

    await verify_tool(library, f"🛠️[cat {temp_file} 100-200 /]")

async def test_cat_tool_file_with_spaces(tmp_path):
    temp_file = create_temp_file(tmp_path, "file with spaces.txt", "line 1\nline 2")

    await verify_tool(library, f"🛠️[cat '{temp_file}' /]")

async def test_cat_tool_range_with_spaces(tmp_path):
    temp_file = create_temp_file(tmp_path, "range spaces.txt", "first\nsecond\nthird")

    await verify_tool(library, f"🛠️[cat '{temp_file}' '1 - 2' /]")

async def test_cat_tool_nonexistent_file_with_range():
    await verify_tool(library, "🛠️[cat /nonexistent/file.txt 1-5 /]")
