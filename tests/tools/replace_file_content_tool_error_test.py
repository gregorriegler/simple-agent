import pytest

from simple_agent.application.tool_library import RawToolCall
from simple_agent.tools.replace_file_content_tool import FileReplacer, ReplaceFileContentTool

pytestmark = pytest.mark.asyncio


async def test_execute_reports_missing_file():
    tool = ReplaceFileContentTool()
    raw_call = RawToolCall(
        name=tool.name,
        arguments="missing.txt single",
        body="old\n@@@\nnew",
    )

    result = await tool.execute(raw_call)

    assert result.success is False
    assert "not found" in result.message


async def test_execute_reports_os_error_for_directory(tmp_path):
    tool = ReplaceFileContentTool()
    raw_call = RawToolCall(
        name=tool.name,
        arguments=f"{tmp_path} single",
        body="old\n@@@\nnew",
    )

    result = await tool.execute(raw_call)

    assert result.success is False
    assert "Error replacing content" in result.message


async def test_execute_reports_no_changes_when_replacement_same(tmp_path):
    tool = ReplaceFileContentTool()
    path = tmp_path / "sample.txt"
    path.write_text("value", encoding="utf-8")
    raw_call = RawToolCall(
        name=tool.name,
        arguments=f"{path} single",
        body="value\n@@@\nvalue",
    )

    result = await tool.execute(raw_call)

    assert result.success is True
    assert "No changes made" in result.message


async def test_parse_arguments_requires_body_separator():
    tool = ReplaceFileContentTool()
    raw_call = RawToolCall(name=tool.name, arguments="file.txt", body="missing")

    parsed, error = tool.parse_arguments(raw_call)

    assert parsed is None
    assert "Missing '@@@'" in error


async def test_parse_arguments_reports_invalid_replace_mode():
    tool = ReplaceFileContentTool()
    raw_call = RawToolCall(name=tool.name, arguments="file.txt invalid", body="a\n@@@\nb")

    parsed, error = tool.parse_arguments(raw_call)

    assert parsed is None
    assert "Invalid replace_mode" in error


async def test_parse_arguments_reports_invalid_argument_syntax():
    tool = ReplaceFileContentTool()
    raw_call = RawToolCall(name=tool.name, arguments='"unclosed', body="a\n@@@\nb")

    parsed, error = tool.parse_arguments(raw_call)

    assert parsed is None
    assert "Error parsing arguments" in error


async def test_parse_arguments_requires_arguments():
    tool = ReplaceFileContentTool()
    raw_call = RawToolCall(name=tool.name, arguments="", body="a\n@@@\nb")

    parsed, error = tool.parse_arguments(raw_call)

    assert parsed is None
    assert error == "No arguments specified"


async def test_file_replacer_rejects_invalid_replace_mode(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("value", encoding="utf-8")
    replacer = FileReplacer(str(path))
    replacer.load_file()

    with pytest.raises(ValueError, match="Invalid replace_mode"):
        replacer.replace("value", "new", "invalid")
