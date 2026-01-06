import textwrap

import pytest
from approvaltests import Options, verify

from tests.test_helpers import all_scrubbers, create_all_tools_for_test

library = create_all_tools_for_test()
pytestmark = pytest.mark.asyncio


async def test_write_todos_creates_markdown_file(tmp_path):
    command = textwrap.dedent("""
    🛠️[write-todos]
    - [ ] Item 1
    - [ ] **Work in progress**
    - [x] Completed
    🛠️[/end]
    """).strip()

    from simple_agent.application.agent_id import AgentId
    from simple_agent.application.agent_types import AgentTypes
    from simple_agent.application.emoji_bracket_tool_syntax import (
        EmojiBracketToolSyntax,
    )
    from simple_agent.application.tool_library_factory import ToolContext
    from simple_agent.tools.all_tools import AllToolsFactory

    agent_id = AgentId("Agent", root=tmp_path)

    tool_context = ToolContext(tool_keys=[], agent_id=agent_id)

    factory = AllToolsFactory(tool_syntax=EmojiBracketToolSyntax())

    async def dummy_spawner(*args):
        pass

    library = factory.create(tool_context, dummy_spawner, AgentTypes([]))

    tool = library.parse_message_and_tools(command)
    result = await library.execute_parsed_tool(tool.tools[0])

    # The file should be at tmp_path / .Agent.todos.md
    content = (tmp_path / ".Agent.todos.md").read_text(encoding="utf-8")
    verify(
        f"Command:\n{command}\n\nResult:\n{result}\n\nFile content:\n--- FILE CONTENT START ---\n{content}\n--- FILE CONTENT END ---",
        options=Options().with_scrubber(all_scrubbers()),
    )
