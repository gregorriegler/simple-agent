import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.tool_library import ToolCall
from simple_agent.infrastructure.file_intents import FileIntents
from simple_agent.tools.bash_tool import BashTool
from simple_agent.tools.communicate_intent_tool import CommunicateIntentTool
from simple_agent.tools.complete_task_tool import CompleteTaskTool
from simple_agent.tools.ls_tool import LsTool
from simple_agent.tools.suggest_tool import SuggestTool
from simple_agent.tools.write_todos_tool import WriteTodosTool

pytestmark = pytest.mark.asyncio


def native_call(name: str, **named) -> ToolCall:
    return ToolCall(name, named)


async def test_bash_runs_the_named_command():
    result = await BashTool().execute(native_call("bash", command="echo hi"))

    assert result.message.endswith("\nhi")


async def test_ls_lists_the_named_path(tmp_path):
    (tmp_path / "a.txt").write_text("")

    result = await LsTool().execute(native_call("ls", path=str(tmp_path)))

    assert "a.txt" in result.message


async def test_complete_task_reports_the_named_summary():
    result = await CompleteTaskTool().execute(
        native_call("complete-task", summary="all done")
    )

    assert result.message == "all done"


async def test_suggest_reads_the_named_suggestion():
    result = await SuggestTool().execute(native_call("suggest", suggestion="rename it"))

    assert result.message == "Suggested: rename it"


async def test_communicate_intent_writes_the_named_intent(tmp_path):
    agent_id = AgentId("Agent", root=tmp_path)

    await CommunicateIntentTool(FileIntents(), agent_id).execute(
        native_call("communicate-intent", intent="extract the parser")
    )

    assert "extract the parser" in agent_id.intent_filename().read_text()


async def test_write_todos_writes_the_named_content(tmp_path):
    todo_file = tmp_path / "todos.md"

    await WriteTodosTool(str(todo_file)).execute(
        native_call("write-todos", content="- [ ] one")
    )

    assert "- [ ] one" in todo_file.read_text()
