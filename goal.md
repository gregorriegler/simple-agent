# Goal: Add Basic File Creation Tool

Add a basic file creation tool to the existing ToolLibrary system:

1. **CreateFileTool** (create): Create new empty files or files with initial content

## Requirements
- Follow the existing tool pattern used by LsTool and CatTool
- Integrate with the ToolLibrary auto-discovery system
- Maintain consistency with the current architecture
- Ensure tools are discoverable by the SystemPromptGenerator
- Add appropriate error handling and validation

## Success Criteria
- New tools are automatically discovered and registered in ToolLibrary
- Tools can be executed via the chat interface with Claude AI
- Tools follow the same patterns as existing static tools
- Tools are documented and testable

## Scenarios

### Create Empty File - REFINED
User wants to create a new empty file in the current directory.
- Input: `/create myfile.txt`
- Expected: New empty file `myfile.txt` is created
- Tool executes: `touch myfile.txt` (Linux/Mac) or equivalent Windows command

**Examples (ordered by simplicity):**
- [x] Create file with single character name: `/create a` → creates empty file `a`
- [x] Create file with simple name and extension: `/create test.txt` → creates empty file `test.txt`

### Create File with Content - REFINED
User wants to create a new file with initial content.
- Input: `/create config.json {"name": "test"}`
- Expected: New file `config.json` is created with the specified JSON content
- Tool writes the content directly to the file

**Examples (ordered by simplicity):**
- [x] Create file with single character content: `/create test.txt a` → creates file `test.txt` with content "a"
- [x] Create file with simple text content: `/create readme.txt Hello World` → creates file `readme.txt` with content "Hello World"
- [x] Create file with newline content: `/create multi.txt "Line 1\nLine 2"` → creates file `multi.txt` with two lines
- [x] Create file with JSON content: `/create config.json {"name": "test"}` → creates file `config.json` with JSON content
- [x] Create file with empty content (explicit): `/create empty.txt ""` → creates file `empty.txt` with empty content

### Create File in Non-existent Directory - REFINED
User wants to create a file in a directory that doesn't exist yet.
- Input: `/create src/utils/helper.py`
- Expected: Directory structure `src/utils/` is created automatically, then `helper.py` is created
- Tool creates parent directories as needed before creating the file

**Examples (ordered by simplicity):**
- [x] Create file in one level deep non-existent directory: `/create src/helper.py "# Helper module"` → creates `src/` directory and `helper.py` with content
- [x] Create file in multiple levels of non-existent directories: `/create src/utils/helpers/helper.py "# Helper module"` → creates all necessary directories and `helper.py` with content

### Handle File Creation Errors - REFINED
User tries to create a file in a location without write permissions.
- Input: `/create /root/restricted.txt`
- Expected: Tool returns error message about insufficient permissions
- Tool handles the error gracefully and provides helpful feedback

**Examples (ordered by simplicity):**
- [ ] Create file in system directory without permissions: `/create /root/test.txt` → returns permission error message

### Handle File Already Exists - REFINED
User tries to create a file that already exists.
- Input: `/create existing.txt`
- Expected: Tool returns error message that file already exists
- Tool prevents accidental overwrites during creation

**Examples (ordered by simplicity):**
- [ ] Create file that already exists: `/create existing.txt` → returns "file already exists" error message

### Handle Invalid File Names - REFINED
User tries to create a file with invalid characters.
- Input: `/create "file<>name.txt"`
- Expected: Tool returns error message about invalid filename
- Tool validates filename before attempting creation

**Examples (ordered by simplicity):**
- [ ] Create file with invalid characters: `/create "file<>name.txt"` → returns invalid filename error message