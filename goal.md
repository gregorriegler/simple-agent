# Goal: Add Basic File Creation and Editing Tools

Add basic file manipulation tools to the existing ToolLibrary system:

1. **CreateFileTool** (create): Create new empty files or files with initial content
2. **WriteFileTool** (modify): Write content to existing files or overwrite file contents

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