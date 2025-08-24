#!/usr/bin/env python
import sys
from tools import ToolLibrary

if __name__ == "__main__":
    command = ' '.join(sys.argv[1:])
    tools = ToolLibrary()
    try:
        tool = tools.parse_tool("/" + command)
        output = tools.execute_parsed_tool(tool)
        print(output)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
