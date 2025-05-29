#!/usr/bin/env python

import sys
from tool_framework import ToolFramework

if __name__ == "__main__":   
    command = ' '.join(sys.argv[1:])
    tool = ToolFramework()
    try:
        output, _ = tool.parse_and_execute("/" + command)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
