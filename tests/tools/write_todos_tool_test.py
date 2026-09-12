import pytest
from approvaltests import Options, verify

from tests.test_helpers import all_scrubbers, execute_call
from tests.tool_calls import write_todos
from tests.transcript import describe_call

pytestmark = pytest.mark.asyncio


async def test_write_todos_creates_markdown_file(tmp_path):
    command = write_todos("- [ ] Item 1\n- [ ] **Work in progress**\n- [x] Completed")

    from simple_agent.application.agent_id import AgentId
    from simple_agent.application.agent_types import AgentTypes
    from simple_agent.application.tool_library_factory import ToolContext
    from simple_agent.application.tool_results import SingleToolResult
    from simple_agent.tools.all_tools import AllToolsFactory

    agent_id = AgentId("Agent", root=tmp_path)

    tool_context = ToolContext(tool_keys=[], agent_id=agent_id)

    factory = AllToolsFactory()

    async def dummy_spawner(agent_type, task_description):
        return SingleToolResult(message="")

    library = factory.create(tool_context, dummy_spawner, AgentTypes([]))

    result = await execute_call(library, command)

    # The file should be at tmp_path / .Agent.todos.md
    content = (tmp_path / ".Agent.todos.md").read_text(encoding="utf-8")
    verify(
        f"Command:\n{describe_call(command)}\n\nResult:\n{result}\n\nFile content:\n--- FILE CONTENT START ---\n{content}\n--- FILE CONTENT END ---",
        options=Options().with_scrubber(all_scrubbers()),
    )
