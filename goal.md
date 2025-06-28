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

**Priority 1: Handle Invalid Symbol Location**
- [x] Add clear error messages when cursor isn't on renameable symbol
- [x] Define supported symbol types (variables, methods, properties, classes)
- [x] Return meaningful error responses instead of silent failures

### Phase 2: Solution-Wide Infrastructure ✅ COMPLETED
- [x] Renames change affected files accross the whole solution

### Phase 3: Expand Symbol Support 📋 PLANNED
**Priority 3: Rename Public Property Across Solution**
- [ ] Add PropertyDeclarationSyntax detection to PerformAsync()
- [ ] Handle both getter and setter references
- [ ] Requires solution-wide infrastructure (Phase 4)

### Phase 4: Naming Conflicts
**Priority 4: Handle Naming Conflict**
- [ ] Add scope-based name collision detection
- [ ] Prevent destructive renames that break code
- [ ] Provide clear conflict resolution messages