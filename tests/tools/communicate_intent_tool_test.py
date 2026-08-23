import textwrap

import pytest
from approvaltests import Options, verify

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.tool_library_factory import ToolContext
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.tools.all_tools import AllToolsFactory
from tests.test_helpers import all_scrubbers

pytestmark = pytest.mark.asyncio


async def test_communicate_intent_writes_intent_file(tmp_path):
    command = textwrap.dedent("""
    🛠️[communicate-intent]
    Extract the tool syntax parser
    🛠️[/end]
    """).strip()

    result = await execute(command, tmp_path)

    content = (tmp_path / ".Agent.intent.md").read_text(encoding="utf-8")
    verify(
        f"Command:\n{command}\n\nResult:\n{result}\n\nFile content:\n--- FILE CONTENT START ---\n{content}\n--- FILE CONTENT END ---",
        options=Options().with_scrubber(all_scrubbers()),
    )


async def test_communicate_intent_overwrites_the_previous_intent(tmp_path):
    await execute("🛠️[communicate-intent]\nFirst goal\n🛠️[/end]", tmp_path)
    await execute("🛠️[communicate-intent]\nSecond goal\n🛠️[/end]", tmp_path)

    content = (tmp_path / ".Agent.intent.md").read_text(encoding="utf-8")

    assert content == "Second goal"


async def execute(command, tmp_path):
    agent_id = AgentId("Agent", root=tmp_path)
    tool_context = ToolContext(tool_keys=["communicate_intent"], agent_id=agent_id)
    factory = AllToolsFactory(tool_syntax=EmojiBracketToolSyntax())

    async def dummy_spawner(agent_type, task_description):
        return SingleToolResult(message="")

    library = factory.create(tool_context, dummy_spawner, AgentTypes([]))
    turn = library.parse_and_resolve(command)
    return await library.execute_tool_call(turn.tool_calls[0])
