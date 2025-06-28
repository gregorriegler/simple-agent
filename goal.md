# Goal: Mutation Testing Tool for Code Modernizer

## Objective
Extend the Code Modernizer toolkit with a **mutation testing tool** that integrates Stryker.NET to provide AI agents with actionable feedback about code quality and test effectiveness.

## Tool Requirements

### Core Functionality
- **Python-based tool** following the existing pattern (similar to [`coverage_tool.py`](modernizer/tools/coverage_tool.py:6))
- **Stryker.NET integration** via process execution
- **Minimal output format** optimized for AI agent consumption (not HTML reports)
- **Integration** with existing [`ToolLibrary`](modernizer/tools/tool_library.py:13) discovery system

### Input Parameters
- Target .NET solution/project path
- Optional: specific files to focus mutation testing on
- Optional: mutation testing configuration (timeout, mutation types, etc.)

### Output Format
The tool should return a structured, minimal format containing:
- **Survived mutants** with location details (file, line, column)
- **Mutation type** (e.g., arithmetic operator change, conditional boundary)
- **Original code** vs **mutated code**
- **Test coverage status** for the mutated line
- **Summary statistics** (total mutants, killed, survived, timeout)

### Expected Output Structure
```json
{
  "success": true,
  "summary": {
    "total_mutants": 45,
    "killed": 38,
    "survived": 5,
    "timeout": 2,
    "mutation_score": 84.4
  },
  "survived_mutants": [
    {
      "file": "Calculator.cs",
      "line": 15,
      "column": 12,
      "mutation_type": "arithmetic_operator",
      "original": "a + b",
      "mutated": "a - b",
      "method": "Add",
      "test_coverage": true
    }
  ]
}
```

### Integration Points
- Discoverable by [`ToolLibrary`](modernizer/tools/tool_library.py:13)
- Executable via [`modernizer.py`](modernizer/modernizer.py:1) chat interface
- Compatible with existing [`runcommand()`](modernizer/tools/tool_library.py:80) infrastructure

## Success Criteria
1. Tool successfully executes Stryker.NET on .NET solutions
2. Parses Stryker output into minimal, agent-friendly format
3. Integrates seamlessly with existing modernizer workflow
4. Provides actionable feedback for AI-driven code improvement
5. Handles errors gracefully with meaningful error messages

## Technical Implementation
- Follow [`BaseTool`](modernizer/tools/base_tool.py) pattern
- Use subprocess to execute Stryker.NET commands
- Parse Stryker JSON output (not HTML) for data extraction
- Implement filtering for specific files/methods when requested
- Add comprehensive error handling for common Stryker failure scenarios

## Scenarios

### Basic Mutation Testing on Simple Calculator - DRAFT
Execute mutation testing on a basic calculator project with simple arithmetic operations (add, subtract, multiply, divide). The project has comprehensive unit tests covering all methods. Expected outcome: tool successfully runs Stryker.NET, parses results, and returns JSON with mutation score and survived mutants.

### Integration with Modernizer Workflow - DRAFT
Use the mutation testing tool through the modernizer chat interface. An AI agent requests mutation testing on a project, receives the results, and uses the survived mutants information to suggest code improvements or additional tests.

### No Tests Available Scenario - DRAFT
Attempt mutation testing on a .NET project that has no unit tests. Stryker.NET should fail gracefully, and the tool should return meaningful error information indicating that tests are required for mutation testing.

### Invalid Project Path Scenario - DRAFT
Execute mutation testing with an invalid or non-existent project path. The tool should handle the error gracefully and return a structured error response with clear messaging about the invalid path.

### Stryker.NET Not Installed Scenario - DRAFT
Attempt to run mutation testing on a system where Stryker.NET is not installed or not accessible. The tool should detect this condition and provide clear installation instructions in the error response.