#!/usr/bin/env python
import sys
from tools import ToolLibrary

if __name__ == "__main__":   
    command = ' '.join(sys.argv[1:])
    tool = ToolLibrary()
    try:
        line, output = tool.parse_and_execute("/" + command)
        print(output)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
