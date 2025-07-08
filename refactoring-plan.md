# Refactoring Plan: Extract Methods from ReplaceInvocationWithInlinedCode

## Goal
Break down the long `ReplaceInvocationWithInlinedCode()` method (37 lines) into smaller, focused methods that each have a single responsibility.

## Steps

- [ ] Extract method `HandleSingleReturnStatement()` for lines 205-208 (single return statement case)
- [ ] Extract method `HandleMultipleStatements()` for lines 210-235 (multiple statements case)  
- [ ] Extract method `ReplaceInBlock()` for lines 222-233 (block replacement logic)
- [ ] Simplify main `ReplaceInvocationWithInlinedCode()` method to orchestrate the extracted methods
- [ ] Run tests to ensure refactoring doesn't break functionality
