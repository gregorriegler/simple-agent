# Goal: Enhance Cat Tool with Line Range Support

## Objective
Adapt the existing [`CatTool`](modernizer/tools/cat_tool.py:3) in the Code Modernizer project to support reading only specific line ranges instead of displaying the entire file content.

## Current State
- The [`CatTool`](modernizer/tools/cat_tool.py:3) currently uses the system `cat -n` command to display entire files with line numbers
- It's integrated into the [`ToolLibrary`](modernizer/tools/tool_library.py:20) as a static tool
- Usage: `/cat filename`

## Desired Enhancement
Enable the cat tool to accept an optional line range parameter in the format `startline-endline`.

### Examples:
- `/cat filename` - Display entire file (current behavior)
- `/cat filename 2-5` - Display only lines 2 through 5
- `/cat filename 10-15` - Display only lines 10 through 15

## Implementation Requirements
1. Maintain backward compatibility - existing usage without range should continue to work
2. Parse the range parameter (e.g., "2-5") to extract start and end line numbers
3. Implement line filtering logic to extract only the specified range
4. Preserve line numbering in the output to maintain context
5. Handle edge cases:
   - Invalid range formats
   - Start line greater than end line
   - Line numbers beyond file length
   - Empty files

## Technical Approach
- Modify the [`CatTool.execute()`](modernizer/tools/cat_tool.py:11) method to accept and parse optional range parameters
- Implement custom line filtering since standard `cat` command doesn't support arbitrary line ranges
- Use Python file reading with line enumeration for precise control
- Update the tool description to reflect the new capability

## Success Criteria
- Tool accepts both old format (`/cat filename`) and new format (`/cat filename 2-5`)
- Correctly displays only the specified line range with proper line numbers
- Handles all edge cases gracefully with appropriate error messages
- Maintains integration with the existing ToolLibrary system