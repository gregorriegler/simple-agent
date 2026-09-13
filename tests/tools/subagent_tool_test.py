import pytest

from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.tool_library import ToolCall
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.tools.subagent_tool import SubagentTool


class SpawnSpy:
    def __init__(self):
        self.calls = []

    async def __call__(self, agent_type, task_description, background):
        self.calls.append((agent_type.raw, task_description, background))
        return SingleToolResult("spawned")


@pytest.mark.asyncio
async def test_subagent_reads_native_named_arguments():
    spawn = SpawnSpy()
    call = ToolCall(
        name="subagent",
        named_arguments={
            "agenttype": "coding",
            "task_description": "say hello world",
            "--background": True,
        },
    )

    await SubagentTool(spawn, AgentTypes.empty()).execute(call)

    assert spawn.calls == [("coding", "say hello world", True)]


def test_the_agenttype_argument_lists_the_available_agent_types():
    tool = SubagentTool(SpawnSpy(), AgentTypes(["software-engineer", "question"]))

    assert tool.arguments["agenttype"].description == (
        "Type of agent to create. Available types: 'software-engineer', 'question'"
    )
