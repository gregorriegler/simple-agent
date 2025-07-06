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

## Scenarios

### Display range from beginning - REFINED
User executes `/cat filename 1-5` and expects to see the first 5 lines of the file with line numbers.

**Examples (ordered by simplicity):**
- [x] Zero lines: `/cat empty.txt 1-5` → displays nothing (file has no lines)
- [x] Single line from beginning: `/cat file.txt 1-1` → displays "1 | first line content"
- [x] Multiple lines from beginning: `/cat file.txt 1-3` → displays first 3 lines with line numbers (1 | first, 2 | second, 3 | third)

### Display specific line range - REFINED
User executes `/cat filename 5-10` and expects to see only lines 5 through 10 of the file with their original line numbers preserved.

**Examples (ordered by simplicity):**
- [x] Specific middle range: `/cat file.txt 5-10` → displays lines 5-10 with original line numbers (5 | Line 5 content, 6 | Line 6 content, etc.)

### Handle invalid range format - REFINED
User executes `/cat filename abc-def` with invalid range format and expects a clear error message explaining the correct format.

**Examples (ordered by simplicity):**
- [x] Invalid range format: `/cat file.txt abc-def` → displays "STDERR: Invalid range format 'abc-def'. Use format 'start-end' (e.g., '1-5')"

### Handle reversed range - REFINED
User executes `/cat filename 10-5` where start line is greater than end line and expects an error message.

**Examples (ordered by simplicity):**
- [x] Reversed range: `/cat file.txt 10-5` → displays "STDERR: Start line (10) cannot be greater than end line (5)"

### Handle range beyond file length - DRAFT
User executes `/cat filename 100-200` on a file with only 50 lines and expects an appropriate message indicating the range is beyond file boundaries.

### Handle non-existent file - DRAFT
User executes `/cat nonexistent.txt 1-5` and expects the same file not found error as the current implementation.