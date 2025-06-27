# Goal: C# Rename Symbol Refactoring Tool

## Overview
Build a C# rename symbol refactoring tool that integrates into the code-modernizer project's RoslynRefactoring component and is accessible through the modernizer's tool library.

## Technical Requirements
- **Technology**: Use Roslyn for C# code analysis and refactoring
- **Scope**: Solution-wide symbol renaming with cross-project reference updates
- **Symbol Types**: Variables, methods, properties, and classes
- **Integration**: Add to existing RoslynRefactoring project in refactoring-tools/
- **Tool Library**: Make available through modernizer's tool library system

## User Interface
Users will provide:
- Solution or project path
- File path containing the symbol
- Cursor location pointing at the symbol to rename
- New symbol name

## Expected Behavior
1. Analyze the solution using Roslyn
2. Identify the symbol at the specified cursor location
3. Find all references to that symbol across the entire solution
4. Rename the symbol and update all references
5. Preserve code semantics and maintain compilation integrity
6. Handle naming conflicts and provide appropriate error handling

## Integration Pattern
Follow the existing pattern of similar refactoring tools already present in the RoslynRefactoring project.

## Scenarios

### Rename Local Variable - DRAFT
User wants to rename a local variable `oldName` to `newName` within a single method. The tool should:
- Identify the variable declaration
- Find all usages within the method scope
- Update all references to use the new name

### Rename Method in Single Class - DRAFT
User wants to rename a private method `DoSomething()` to `ProcessData()` within one class. The tool should:
- Identify the method declaration
- Find all calls to this method within the same class
- Update the method name and all call sites

### Rename Public Property Across Solution - DRAFT
User wants to rename a public property `CustomerName` to `ClientName` in a class that's used across multiple projects. The tool should:
- Identify the property declaration
- Find all references across all projects in the solution
- Update the property name and all usage sites
- Handle both getter and setter references

### Rename Class Across Solution - DRAFT
User wants to rename a class `OrderProcessor` to `PaymentProcessor`. The tool should:
- Identify the class declaration
- Find all references across the solution (instantiations, inheritance, type parameters)
- Update all references to use the new class name

### Handle Naming Conflict - DRAFT
User attempts to rename a variable to a name that already exists in the same scope. The tool should:
- Detect the naming conflict
- Provide a clear error message
- Prevent the rename operation

### Handle Invalid Symbol Location - DRAFT
User provides a cursor location that doesn't point to a renameable symbol (e.g., keyword, comment). The tool should:
- Detect that no valid symbol exists at the location
- Provide a clear error message explaining what types of symbols can be renamed

### Handle Compilation Errors - DRAFT
User attempts to rename a symbol in code that doesn't compile. The tool should:
- Detect compilation issues in the solution
- Provide appropriate error handling or warnings
- Potentially allow renaming with warnings about existing compilation issues