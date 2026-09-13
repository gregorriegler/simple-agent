import pytest
from approvaltests import Options, verify

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.tool_library_factory import ToolContext
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.file_intents import FileIntents
from simple_agent.infrastructure.file_todos import FileTodos
from simple_agent.tools.all_tools import AllToolsFactory
from tests.test_helpers import all_scrubbers, execute_call
from tests.tool_calls import communicate_intent
from tests.transcript import describe_call

pytestmark = pytest.mark.asyncio


async def test_communicate_intent_writes_intent_file(tmp_path):
    command = communicate_intent("Extract the tool syntax parser")

    result = await execute(command, tmp_path)

    content = (tmp_path / ".Agent.intent.md").read_text(encoding="utf-8")
    verify(
        f"Command:\n{describe_call(command)}\n\nResult:\n{result}\n\nFile content:\n--- FILE CONTENT START ---\n{content}\n--- FILE CONTENT END ---",
        options=Options().with_scrubber(all_scrubbers()),
    )


async def test_communicate_intent_overwrites_the_previous_intent(tmp_path):
    await execute(communicate_intent("First goal"), tmp_path)
    await execute(communicate_intent("Second goal"), tmp_path)

    content = (tmp_path / ".Agent.intent.md").read_text(encoding="utf-8")

    assert content == "Second goal"


async def execute(command, tmp_path):
    agent_id = AgentId("Agent", root=tmp_path)
    tool_context = ToolContext(tool_keys=["communicate_intent"], agent_id=agent_id)
    factory = AllToolsFactory(FileIntents(), FileTodos())

    async def dummy_spawner(agent_type, task_description):
        return SingleToolResult(message="")

    library = factory.create(tool_context, dummy_spawner, AgentTypes([]))
    return await execute_call(library, command)
