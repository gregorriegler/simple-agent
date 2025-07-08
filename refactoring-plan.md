# Refactoring Plan

## Identified Issue to Improve

### Long Method - InlineMethod.PerformAsync()
The [`PerformAsync()`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:18) method is 37 lines long and handles multiple responsibilities:
- Document preparation (getting syntax root and semantic model)
- Cursor position resolution and node finding
- Method invocation discovery and validation
- Method symbol resolution and declaration finding
- Method body extraction and transformation
- Parameter mapping creation
- Method body inlining
- Final code replacement

This method violates the Single Responsibility Principle and makes the code harder to understand, test, and maintain.

## Refactoring Tasks

- [x] Extract method: Create `PrepareDocumentAsync()` to handle document preparation (lines 20-24)
- [x] Extract method: Create `FindInvocationAtCursor()` to handle cursor position resolution and invocation finding (lines 26-31)
- [x] Extract method: Create `ValidateAndGetMethodSymbol()` to handle method symbol validation (lines 33-35)
- [x] Extract method: Create `PrepareMethodForInlining()` to handle method declaration finding and body preparation (lines 37-46)
- [x] Extract method: Create `PerformInlining()` to handle the actual inlining process (lines 48-52)
- [ ] Refactor `PerformAsync()` to orchestrate these smaller methods, making the main flow clearer and easier to follow
