# Refactoring Plan: Extract Test Helper Methods

## Goal
Remove duplicated code in [`InlineMethodTests.cs`](refactoring-tools/RoslynRefactoring.Tests/InlineMethodTests.cs) by extracting common workspace and document creation patterns into reusable helper methods.

## Steps

- [ ] Extract method `CreateWorkspaceWithProject()` to eliminate duplication in workspace/project setup (lines 42-44, 82-83)
- [ ] Extract method `CreateDocumentInProject()` to simplify single document creation
- [ ] Extract method `CreateTwoDocumentProject()` to handle the cross-file test setup pattern
- [ ] Update all test methods to use the new helper methods
- [ ] Run tests to ensure refactoring doesn't break functionality
