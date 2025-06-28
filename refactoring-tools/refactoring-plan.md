# Refactoring Plan

## Identified Improvements

### RenameSymbol.cs
- [ ] Remove code duplication: IdentifyAndRenameSymbol and IdentifyAndRenameSymbolSolutionWide have nearly identical logic
- [x] Extract method for token validation (repeated null checks and error messages)
- [ ] Long method: RenameMethodSolutionWide is doing too many things (finding declarations, finding calls, replacing nodes)
- [x] Extract method for finding method declarations across solution
- [x] Extract method for finding method calls across solution
- [x] Remove unused method: IdentifyAndRenameSymbol is no longer used since we always use solution-wide approach
- [x] Improve variable naming: 'nodesToRename' could be more specific like 'methodReferences'

### RenameSymbolSolutionWideTests.cs
- [x] Extract method for solution creation with multiple files (could be reused in other tests) - Already well implemented
- [x] Long parameter list in CreateSolutionWithFiles (uses params but could be cleaner) - Uses params appropriately for variable arguments
