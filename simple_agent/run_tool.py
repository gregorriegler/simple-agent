#!/usr/bin/env python
import sys
from simple_agent.tools import AllTools

if __name__ == "__main__":
    command = ' '.join(sys.argv[1:])
    tools = AllTools()
    try:
        tool = tools.parse_message_and_tools(f"🛠️ {command}")
        if not tool:
            print(f"Unknown tool: {command}")
            sys.exit(1)
        output = tools.execute_parsed_tool(tool)
        print(output)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
