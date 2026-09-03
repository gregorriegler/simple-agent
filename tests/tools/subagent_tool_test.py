import pytest

from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.tool_library import RawToolCall
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.tools.subagent_tool import SubagentTool

pytestmark = pytest.mark.asyncio


class SpawnSpy:
    def __init__(self):
        self.calls = []

    async def __call__(self, agent_type, task_description, is_async):
        self.calls.append((agent_type.raw, task_description, is_async))
        return SingleToolResult("spawned")


async def test_subagent_reads_native_named_arguments():
    spawn = SpawnSpy()
    call = RawToolCall(
        name="subagent",
        arguments="coding say hello world True",
        named_arguments={
            "agenttype": "coding",
            "task_description": "say hello world",
            "--async": True,
        },
    )

    await SubagentTool(spawn, AgentTypes.empty()).execute(call)

    assert spawn.calls == [("coding", "say hello world", True)]
