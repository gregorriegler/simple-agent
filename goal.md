# Goal: Auto-detect Project Files for Entry Point Analysis

## Objective
Enhance the entry-point-analysis tool to automatically find and use .sln or .csproj files when only a directory path is provided, eliminating the need to specify the project file explicitly.

## Current State
- The entry-point-analysis tool currently requires explicit specification of the .csproj file path
- Users must know and provide the exact project file name
- This creates friction when analyzing projects where the .csproj name isn't immediately obvious

## Desired Enhancement
Enable the entry-point-analysis tool to accept just a directory path and automatically locate the appropriate project file to analyze.

### Behavior:
- When given a directory path, search for project files in this priority order:
  1. First .sln file found (solution files take priority)
  2. First .csproj file found (if no .sln exists)
- Search only in the immediate directory provided (no recursive search)
- Use the found file for entry point analysis

### Examples:
- `/entry-point-analysis /path/to/project` - Automatically finds and uses MyProject.sln or MyProject.csproj
- `/entry-point-analysis /path/to/project/MyProject.csproj` - Continue to support explicit file specification (backward compatibility)

## Implementation Requirements
1. Maintain backward compatibility - existing usage with explicit file paths should continue to work
2. Implement directory scanning logic to find .sln files first, then .csproj files
3. Handle edge cases:
   - Directory with no .sln or .csproj files
   - Directory that doesn't exist
   - Permission issues accessing the directory
4. Provide clear error messages when no suitable project files are found
5. Only search in the immediate directory (no subdirectory traversal)

## Technical Approach
- Modify the entry-point-analysis tool's argument parsing to detect when a directory vs. file is provided
- Implement file discovery logic with .sln priority over .csproj

## Success Criteria
- Tool accepts both directory paths and explicit file paths
- Automatically finds and uses the first .sln file, or first .csproj if no .sln exists
- Maintains all existing functionality when explicit file paths are provided
- Provides helpful error messages when no project files are found
- Works seamlessly with the existing tool discovery and execution system

## Scenarios

### [x] Basic Directory Analysis - REFINED
User provides a directory path containing a single .csproj file. The tool automatically detects and uses the .csproj file for entry point analysis.

### [ ] Solution File Priority - REFINED
User provides a directory path containing both .sln and .csproj files. The tool automatically selects the .sln file (higher priority) for analysis.
