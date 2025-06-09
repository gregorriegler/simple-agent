# Refactoring Plan

## Dead Code Removal

- [x] Remove the unused `FindEntryPointsInDocumentAsync` method from `EntryPointFinder.cs` - this private method is never called and can be safely deleted
- [x] Remove redundant reachable methods calculation in `TryCreateEntryPoint` method - this calculation is overwritten later by `CalculateReachableMethodsCount`, making the local calculation dead code
- [x] Remove redundant `&& methodSymbol.ContainingType != null` check - in all test scenarios, when methodSymbol is not null, ContainingType is also never null
