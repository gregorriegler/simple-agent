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
- [ ] Create file with simple text content: `/create readme.txt Hello World` → creates file `readme.txt` with content "Hello World"
- [ ] Create file with multi-word content: `/create note.txt This is a test note` → creates file `note.txt` with content "This is a test note"
- [ ] Create file with newline content: `/create multi.txt "Line 1\nLine 2"` → creates file `multi.txt` with two lines
- [ ] Create file with JSON content: `/create config.json {"name": "test"}` → creates file `config.json` with JSON content
- [ ] Create file with empty content (explicit): `/create empty.txt ""` → creates file `empty.txt` with empty content

### Create File in Non-existent Directory - DRAFT
User wants to create a file in a directory that doesn't exist yet.
- Input: `/create src/utils/helper.py`
- Expected: Directory structure `src/utils/` is created automatically, then `helper.py` is created
- Tool creates parent directories as needed before creating the file

### Handle File Creation Errors - DRAFT
User tries to create a file in a location without write permissions.
- Input: `/create /root/restricted.txt`
- Expected: Tool returns error message about insufficient permissions
- Tool handles the error gracefully and provides helpful feedback

### Handle File Already Exists - DRAFT
User tries to create a file that already exists.
- Input: `/create existing.txt`
- Expected: Tool returns error message that file already exists
- Tool prevents accidental overwrites during creation

### Handle Invalid File Names - DRAFT
User tries to create a file with invalid characters.
- Input: `/create "file<>name.txt"`
- Expected: Tool returns error message about invalid filename
- Tool validates filename before attempting creation