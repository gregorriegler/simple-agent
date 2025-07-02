# Goal: Implement Edit-File Tool

## Objective
Implement a Python-based edit-file tool that allows selecting a block of lines, deleting their contents, and inserting replacement content.

## Core Functionality
The tool should enable:
- Select a range of lines in a file (e.g., lines 5-10)
- Delete the contents of those selected lines
- Insert new content in place of the deleted lines
- Save the modified file

## Requirements
- Create a Python tool that integrates with the existing ToolLibrary system
- Support line-based editing operations (select, delete, insert)
- Handle file reading and writing safely
- Provide clear error messages for invalid operations
- Follow the project's tool architecture patterns

## Implementation Details
- Tool should be discoverable by the ToolLibrary system
- Accept parameters: file_path, start_line, end_line, new_content
- Validate line ranges and file existence
- Preserve file encoding and line endings
- Include proper error handling

## Success Criteria
- Tool can select and replace content in specified line ranges
- Integrates with the modernizer.sh interface
- Provides reliable file modification functionality
- Follows project coding standards and patterns

## Scenarios

### Replace Single Line - REFINED
Edit a file by replacing one line with new content.
- File: `test.py` with content "old_variable = 5"
- Replace line 1 with "new_variable = 10"
- Expected: File contains "new_variable = 10"

**Examples (ordered by simplicity):**
- [x] Replace single character in one-line file: file with "a", replace line 1 with "b"
- [ ] Replace single word in one-line file: file with "old", replace line 1 with "new"

### Replace Multiple Consecutive Lines - DRAFT
Edit a file by replacing a block of consecutive lines.
- File: `config.py` with 5 lines of configuration
- Replace lines 2-4 with new configuration block
- Expected: Lines 2-4 are replaced, lines 1 and 5 remain unchanged

### Replace 1 Line with 3 Other Lines - DRAFT
Replace a single line with multiple lines of content.
- File: `code.py` with "# TODO: implement function"
- Replace line 5 with 3 lines of actual function implementation
- Expected: Single line becomes 3 lines, total file length increases

### Insert Content by Replacing Empty Lines - DRAFT
Replace empty lines with new content.
- File: `template.py` with empty lines 3-5
- Replace lines 3-5 with function definition
- Expected: Function is inserted where empty lines were

### Invalid Line Range Error - DRAFT
Attempt to edit lines that don't exist in the file.
- File: `short.py` with 5 lines
- Try to replace lines 10-15
- Expected: Clear error message about invalid line range

### File Not Found Error - DRAFT
Attempt to edit a non-existent file.
- Try to edit `nonexistent.py`
- Expected: Clear error message about file not found

### Empty File Handling - DRAFT
Attempt to edit an empty file.
- File: `empty.py` with 0 lines
- Try to replace lines 1-2
- Expected: Clear error message about empty file or invalid range