# Goal: Code Coverage Analysis Tool

## Objective
Create a new analysis tool for the code-modernizer that provides feedback on code coverage by generating coverage data and identifying uncovered code sections.

## Specifications

### Core Functionality
- **Generate Coverage Data**: Run `dotnet test` with coverlet to generate code coverage reports
- **Analyze Coverage**: Parse the coverage data to identify specific uncovered code sections
- **Highlight Uncovered Code**: Present clear feedback showing which lines, methods, or branches are not covered by tests

### Technical Requirements
- **Language Support**: C# only (using dotnet test + coverlet)
- **Tool Implementation**: Python tool that inherits from BaseTool (following existing pattern)
- **Integration**: Static tool added to ToolLibrary like TestTool, LsTool, CatTool (not auto-discovered)
- **Output Format**: Clear identification and highlighting of uncovered code sections

### Implementation Approach
1. Create Python coverage tool inheriting from BaseTool
2. Execute `dotnet test` with coverlet via subprocess to generate coverage data
3. Parse XML/JSON coverage reports in Python to extract uncovered code information
4. Format output to clearly highlight uncovered sections for developer feedback
5. Add tool to static_tools list in ToolLibrary.__init__ (similar to TestTool)

### Success Criteria
- Tool is automatically discovered by the modernizer system
- Successfully runs dotnet test with coverage collection
- Accurately identifies and reports uncovered code sections