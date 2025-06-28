# Refactoring Plan

## Identified Improvements

### RenameSymbol.cs
- [ ] Remove code duplication: IdentifyAndRenameSymbol and IdentifyAndRenameSymbolSolutionWide have nearly identical logic
- [ ] Extract method for token validation (repeated null checks and error messages)
- [ ] Long method: RenameMethodSolutionWide is doing too many things (finding declarations, finding calls, replacing nodes)
- [ ] Extract method for finding method declarations across solution
- [ ] Extract method for finding method calls across solution
- [ ] Remove unused method: IdentifyAndRenameSymbol is no longer used since we always use solution-wide approach
- [ ] Improve variable naming: 'nodesToRename' could be more specific like 'methodReferences'

### RenameSymbolSolutionWideTests.cs
- [ ] Extract method for solution creation with multiple files (could be reused in other tests)
- [ ] Long parameter list in CreateSolutionWithFiles (uses params but could be cleaner)
