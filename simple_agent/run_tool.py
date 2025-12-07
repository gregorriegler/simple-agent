#!/usr/bin/env python
import sys

from simple_agent.tools import AllTools

if __name__ == "__main__":
    command = ' '.join(sys.argv[1:])

    def dummy_spawner(agent_type, task_description):
        raise NotImplementedError("Subagent spawning not available in run_tool.py")

    tools = AllTools(tool_context=None, spawner=dummy_spawner)
    try:
        result = tools.parse_message_and_tools(f"🛠️ {command}")
        if not result.tools:
            print(f"Unknown tool: {command}")
            sys.exit(1)
        output = tools.execute_parsed_tool(result.tools[0])
        print(output)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
