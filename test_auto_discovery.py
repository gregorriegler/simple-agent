#!/usr/bin/env python3
"""
Test script to demonstrate the auto-discovery of refactoring tool arguments
from C# classes using reflection.
"""

import sys
import os
sys.path.append('modernizer')

from tools.tool_library import ToolLibrary

def main():
    print("=== Refactoring Tool Auto-Discovery Demo ===\n")
    
    # Initialize the tool library (this will auto-discover C# tools)
    tool_library = ToolLibrary()
    
    print("1. Listing all available tools:")
    print(tool_library.get_tool_info())
    print("\n" + "="*60 + "\n")
    
    print("2. Detailed information about refactoring tools:")
    print(tool_library.get_refactoring_tools_info())
    print("\n" + "="*60 + "\n")
    
    print("3. Testing individual tool information:")
    test_tools = ['extract-method', 'inline-method', 'extract-collaborator-interface', 'break-hard-dependency']
    
    for tool_name in test_tools:
        print(f"\n--- {tool_name.upper()} ---")
        tool = tool_library.tool_dict.get(tool_name)
        if tool and hasattr(tool, 'info'):
            print(f"Description: {tool.description}")
            print(f"Arguments: {tool.arguments}")
            print(f"Raw info from C#: {tool.info}")
        else:
            print(f"Tool {tool_name} not found or not auto-generated")
    
    print("\n" + "="*60 + "\n")
    print("4. Testing argument validation:")
    
    extract_method_tool = tool_library.tool_dict.get('extract-method')
    if extract_method_tool and hasattr(extract_method_tool, 'validate_arguments'):
        # Test with wrong number of arguments
        is_valid, message = extract_method_tool.validate_arguments("arg1 arg2")
        print(f"Validation with 2 args: Valid={is_valid}")
        if not is_valid:
            print(f"Error message:\n{message}")
        
        # Test with correct number of arguments
        is_valid, message = extract_method_tool.validate_arguments("project.csproj file.cs 1:1-2:10 NewMethod")
        print(f"\nValidation with 4 args: Valid={is_valid}, Message={message}")

if __name__ == "__main__":
    main()