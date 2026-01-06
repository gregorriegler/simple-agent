from simple_agent.application.tool_library import ParsedTool, RawToolCall
from simple_agent.application.tool_results import (
    ManyToolsResult,
    SingleToolResult,
    ToolResultStatus,
)


class DummyTool:
    def __str__(self):
        return "DummyTool"


def test_single_tool_result_cancelled_when_status_cancelled():
    result = SingleToolResult(status=ToolResultStatus.CANCELLED)

    assert result.cancelled is True


def test_many_tools_result_exposes_last_result_display_fields():
    tool = ParsedTool(RawToolCall(name="dummy", arguments=""), DummyTool())
    inner_result = SingleToolResult(
        message="done",
        display_title="Title",
        display_body="Body",
        display_language="text",
    )
    results = ManyToolsResult()

    results.add(tool, inner_result)

    assert results.display_title == "Title"
    assert results.display_body == "Body"
    assert results.display_language == "text"


def test_many_tools_result_reports_failure_when_cancelled():
    tool = ParsedTool(RawToolCall(name="dummy", arguments=""), DummyTool())
    results = ManyToolsResult()
    results.add(tool, SingleToolResult())

    results.mark_cancelled(tool)

    assert results.success is False
