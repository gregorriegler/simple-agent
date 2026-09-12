from simple_agent.application.tool_library import ToolCall


def test_resolving_pairs_a_call_with_its_tool_and_leaves_the_call_as_it_is(
    tool_library,
):
    call = ToolCall("cat", {"filename": "my notes.md"})

    turn = tool_library.resolve_tool_calls([call], "reading")

    assert turn.message == "reading"
    assert turn.invocations[0].call is call
    assert type(turn.invocations[0].tool).__name__ == "CatTool"
