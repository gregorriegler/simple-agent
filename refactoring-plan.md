# Refactoring Plan: Extract Methods from ReplaceInvocationWithInlinedCode

## Goal
Break down the long `ReplaceInvocationWithInlinedCode()` method (37 lines) into smaller, focused methods that each have a single responsibility.

## Steps

- [x] Extract method `HandleSingleReturnStatement()` for lines 205-208 (single return statement case)
- [x] Extract method `HandleMultipleStatements()` for lines 210-235 (multiple statements case)
- [x] Extract method `ReplaceInBlock()` for lines 222-233 (block replacement logic)
- [x] Simplify main `ReplaceInvocationWithInlinedCode()` method to orchestrate the extracted methods
- [x] Run tests to ensure refactoring doesn't break functionality
