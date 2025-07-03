# Refactoring Plan

## Identified Issues to Improve

### 1. Long Method - CatTool.execute()
The [`CatTool.execute()`](modernizer/tools/cat_tool.py:11) method is 48 lines long and handles multiple responsibilities:
- Argument parsing
- Range validation
- File reading
- Line filtering
- Output formatting

### 2. Feature Envy - CatTool accessing file system directly
The [`CatTool`](modernizer/tools/cat_tool.py:3) directly opens and reads files instead of using the `runcommand` abstraction like other tools.

### 3. Long Parameter List - ToolLibrary constructor
The [`ToolLibrary.__init__()`](modernizer/tools/tool_library.py:17) method creates many tools inline, making it hard to read and maintain.

## Refactoring Tasks

- [x] Extract method: Create `_parse_arguments()` method in CatTool to handle argument parsing
- [x] Extract method: Create `_validate_range()` method in CatTool to handle range validation
- [ ] Extract method: Create `_read_file_range()` method in CatTool to handle file reading and line filtering
- [ ] Extract method: Create `_format_output()` method in CatTool to handle output formatting
- [ ] Extract method: Create `_create_static_tools()` method in ToolLibrary to reduce constructor complexity
- [ ] Extract method: Create `_discover_dynamic_tools()` method in ToolLibrary to group tool discovery logic
- [ ] Improve variable names: Rename `cmd` to `command` in ToolLibrary.parse_and_execute()
- [ ] Improve variable names: Rename `arg` to `arguments` in ToolLibrary.parse_and_execute()
- [ ] Remove dead code: Remove unused `description` attribute assignment in BaseTool if not used