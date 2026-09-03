from simple_agent.application.tool_library import RawToolCall, ToolCall
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
    tool = ToolCall(RawToolCall(name="dummy", arguments=""), DummyTool())
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


def test_many_tools_result_exposes_per_tool_name_and_output():
    results = ManyToolsResult()
    results.add(
        ToolCall(RawToolCall(name="bash", arguments="ls"), DummyTool()),
        SingleToolResult(message="a.txt"),
    )
    results.add(
        ToolCall(RawToolCall(name="cat", arguments="a.txt"), DummyTool()),
        SingleToolResult(message="hello"),
    )

    assert [(call.name, output) for call, output in results.tool_results] == [
        ("bash", "a.txt"),
        ("cat", "hello"),
    ]


def test_many_tools_result_message_is_the_last_results_message():
    results = ManyToolsResult()
    results.add(
        ToolCall(RawToolCall(name="bash", arguments="ls"), DummyTool()),
        SingleToolResult(message="a.txt"),
    )
    results.add(
        ToolCall(RawToolCall(name="cat", arguments="a.txt"), DummyTool()),
        SingleToolResult(message="hello"),
    )

    assert results.message == "hello"


def test_many_tools_result_reports_failure_when_cancelled():
    tool = ToolCall(RawToolCall(name="dummy", arguments=""), DummyTool())
    results = ManyToolsResult()
    results.add(tool, SingleToolResult())

    results.mark_cancelled(tool)

    assert results.success is False
