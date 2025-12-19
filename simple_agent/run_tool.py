#!/usr/bin/env python
import asyncio
import sys

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.tool_library_factory import ToolContext
from simple_agent.infrastructure.agent_library import BuiltinAgentLibrary
from simple_agent.tools import AllTools

if __name__ == "__main__":
    command = ' '.join(sys.argv[1:])

    def dummy_spawner(agent_type, task_description):
        raise NotImplementedError("Subagent spawning not available in run_tool.py")

    tool_syntax = EmojiBracketToolSyntax()
    agent_library = BuiltinAgentLibrary()
    tool_context = ToolContext([], AgentId("Agent"))
    agent_types = AgentTypes(agent_library.list_agent_types())
    tools = AllTools(
        tool_context=tool_context,
        spawner=dummy_spawner,
        agent_types=agent_types,
        tool_syntax=tool_syntax,
    )
    try:
        result = tools.parse_message_and_tools(f"🛠️ {command}")
        if not result.tools:
            print(f"Unknown tool: {command}")
            sys.exit(1)
        output = asyncio.run(tools.execute_parsed_tool(result.tools[0]))
        print(output)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
