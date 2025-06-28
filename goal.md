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

## Implementation Plan

### Phase 1: Foundation & Error Handling ✅ COMPLETED
- [x] **Rename Local Variable** - All scenarios implemented and working
- [x] **Rename Method in Single Class** - All scenarios implemented and working

### Phase 2: Error Handling & User Experience 🚧 NEXT
**Priority 1: Handle Invalid Symbol Location**
- [x] Add clear error messages when cursor isn't on renameable symbol
- [x] Define supported symbol types (variables, methods, properties, classes)
- [x] Return meaningful error responses instead of silent failures

**Priority 2: Handle Naming Conflict**
- [ ] Add scope-based name collision detection
- [ ] Prevent destructive renames that break code
- [ ] Provide clear conflict resolution messages

### Phase 3: Expand Symbol Support 📋 PLANNED
**Priority 3: Rename Public Property Across Solution**
- [ ] Add PropertyDeclarationSyntax detection to PerformAsync()
- [ ] Handle both getter and setter references
- [ ] Requires solution-wide infrastructure (Phase 4)

### Phase 4: Solution-Wide Infrastructure 🔮 FUTURE
**Priority 4: Solution-Wide Operations**
- [ ] Upgrade from single Document to Solution operations
- [ ] Implement cross-project reference finding
- [ ] Enable multi-document updates

**Priority 5: Rename Class Across Solution**
- [ ] Add ClassDeclarationSyntax detection
- [ ] Handle instantiations, inheritance, type parameters
- [ ] Build on solution-wide infrastructure

### Phase 5: Robustness 🔮 FUTURE
**Priority 6: Handle Compilation Errors**
- [ ] Add pre-rename compilation validation
- [ ] Provide warnings about existing issues
- [ ] Allow renaming with appropriate warnings

## Completed Scenarios

### Rename Local Variable - ✅ IMPLEMENTED
User wants to rename a local variable `oldName` to `newName` within a single method. The tool should:
- Identify the variable declaration
- Find all usages within the method scope
- Update all references to use the new name

**Examples (all working):**
- [x] **Zero usage**: Rename unused local variable `int unused = 5;` to `int temp = 5;`
- [x] **One usage**: Rename variable with single usage `int count = 0; return count;`
- [x] **Many usages**: Rename variable used multiple times in method
- [x] **Variable in different scopes**: Rename variable that shadows outer scope variable
- [x] **Variable in loop**: Rename loop variable `for(int i = 0; i < 10; i++)`

### Rename Method in Single Class - ✅ IMPLEMENTED
User wants to rename a private method `DoSomething()` to `ProcessData()` within one class. The tool should:
- Identify the method declaration
- Find all calls to this method within the same class
- Update the method name and all call sites

**Examples (all working):**
- [x] **Zero usage**: Rename unused private method
- [x] **One usage**: Rename private method called once
- [x] **Many usages**: Rename private method called multiple times within same class
- [x] **Method with parameters**: Rename method with parameters