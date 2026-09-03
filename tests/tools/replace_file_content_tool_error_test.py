import pytest

from simple_agent.application.tool_library import RawToolCall
from simple_agent.tools.replace_file_content_tool import (
    FileReplacer,
    ReplaceFileContentTool,
)

pytestmark = pytest.mark.asyncio


def replace_call(filename, replace_mode, content):
    named = {"filename": filename, "content": content}
    if replace_mode:
        named["replace_mode"] = replace_mode
    return RawToolCall(
        name=ReplaceFileContentTool.name,
        arguments=f"{filename} {replace_mode}".strip(),
        body=content,
        named_arguments=named,
    )


async def test_execute_reports_missing_file():
    tool = ReplaceFileContentTool()
    raw_call = replace_call("missing.txt", "single", "old\n@@@\nnew")

    result = await tool.execute(raw_call)

    assert result.success is False
    assert "not found" in result.message


async def test_execute_reports_os_error_for_directory(tmp_path):
    tool = ReplaceFileContentTool()
    raw_call = replace_call(str(tmp_path), "single", "old\n@@@\nnew")

    result = await tool.execute(raw_call)

    assert result.success is False
    assert "Error replacing content" in result.message


async def test_execute_reports_no_changes_when_replacement_same(tmp_path):
    tool = ReplaceFileContentTool()
    path = tmp_path / "sample.txt"
    path.write_text("value", encoding="utf-8")
    raw_call = replace_call(str(path), "single", "value\n@@@\nvalue")

    result = await tool.execute(raw_call)

    assert result.success is True
    assert "No changes made" in result.message


async def test_parse_arguments_requires_body_separator():
    tool = ReplaceFileContentTool()
    raw_call = replace_call("file.txt", "", "missing")

    parsed, error = tool.parse_arguments(raw_call)

    assert parsed is None
    assert error is not None
    assert "Missing '@@@'" in error


async def test_parse_arguments_reports_invalid_replace_mode():
    tool = ReplaceFileContentTool()
    raw_call = replace_call("file.txt", "invalid", "a\n@@@\nb")

    parsed, error = tool.parse_arguments(raw_call)

    assert parsed is None
    assert error is not None
    assert "Invalid replace_mode" in error


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
