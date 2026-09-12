import pytest
from approvaltests import Options, verify

from tests.test_helpers import all_scrubbers, execute_call, temp_directory
from tests.tool_calls import create_file
from tests.transcript import describe_call

pytestmark = pytest.mark.asyncio


async def test_create_tool_single_character_name(tmp_path, tool_library):
    await verify_create_tool(tool_library, create_file("a"), "a", tmp_path=tmp_path)


async def test_create_tool_simple_name_with_extension(tmp_path, tool_library):
    await verify_create_tool(
        tool_library, create_file("test.txt"), "test.txt", tmp_path=tmp_path
    )


async def test_create_file_in_nonexistent_directory(tmp_path, tool_library):
    await verify_create_tool(
        tool_library,
        create_file("src/utils/helper.py"),
        "src/utils/helper.py",
        tmp_path=tmp_path,
    )


async def test_create_file_already_exists(tmp_path, tool_library):
    with temp_directory(tmp_path):
        await execute_call(tool_library, create_file("existing.txt"))

        result = await execute_call(tool_library, create_file("existing.txt"))
        assert (
            "already exists" in result.message.lower()
            or "exists" in result.message.lower()
        )


async def test_create_tool_multi_line_content(tmp_path, tool_library):
    await verify_create_tool(
        tool_library,
        create_file("a", "First Line\nSecond Line\nThird Line"),
        "a",
        tmp_path=tmp_path,
    )


async def verify_create_tool(tool_library, command, expected_filename, tmp_path):
    with temp_directory(tmp_path):
        result = await execute_call(tool_library, command)

        with open(expected_filename, encoding="utf-8") as f:
            actual_content = f.read()
            file_info = f"File created: {expected_filename}\nFile content:\n--- FILE CONTENT START ---\n{actual_content}\n--- FILE CONTENT END ---"

        verify(
            f"Command:\n{describe_call(command)}\n\nResult:\n{result}\n\n{file_info}",
            options=Options().with_scrubber(all_scrubbers()),
        )
