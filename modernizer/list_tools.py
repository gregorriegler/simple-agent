#!/usr/bin/env python
import sys
from tools import ToolLibrary

if __name__ == "__main__":   
    tool = ToolLibrary()
    try:
        if len(sys.argv) > 1:
            tool_name = sys.argv[1]
            output = tool.get_tool_info(tool_name)
        else:
            output = tool.get_tool_info()
        print(output)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)