# Refactoring Plan: Extract Methods from PerformAsync

## Goal
Break down the long [`PerformAsync`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:18) method (30 lines) into smaller, focused methods with single responsibilities.

## Steps

- [x] Extract method `ProcessAllInvocations()` to handle finding and processing all invocations (lines 32-46)
- [x] Extract method `ValidateInvocationContext()` to handle initial validation steps (lines 20-30)
- [x] Update [`PerformAsync`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:18) to use the new extracted methods
- [x] Run tests to ensure refactoring doesn't break functionality
