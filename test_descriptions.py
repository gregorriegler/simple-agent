#!/usr/bin/env python3

import sys
sys.path.append('modernizer')

from tools.tool_library import ToolLibrary

def test_descriptions():
    library = ToolLibrary()
    
    refactoring_tools = [
        'extract-method',
        'inline-method', 
        'break-hard-dependency',
        'extract-collaborator-interface'
    ]
    
    for tool_name in refactoring_tools:
        tool = library.tool_dict.get(tool_name)
        if tool and hasattr(tool, 'description'):
            print(f"{tool_name}: {tool.description}")
        else:
            print(f"{tool_name}: No description property found")

if __name__ == "__main__":
    test_descriptions()