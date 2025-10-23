#!/usr/bin/env python
import sys
from simple_agent.tools import AllTools
from simple_agent.tools.subagent_context import SubagentContext

if __name__ == "__main__":
    command = ' '.join(sys.argv[1:])

    subagent_context = SubagentContext(
        None,
        0,
        "Tool"
    )

    tools = AllTools(subagent_context)
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
