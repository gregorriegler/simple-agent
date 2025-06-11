# Refactoring Plan: Remove Loops and Where Clauses from Tests

## Tasks

- [ ] Replace `entryPoints.First()` calls with direct indexing `entryPoints[0]`
- [ ] Replace `entryPoints.Select().ToList()` with direct property access using indices
- [ ] Replace `entryPoints.First(ep => predicate)` with direct indexing based on known test data
- [ ] Replace `entryPoints.FirstOrDefault(ep => predicate)` with direct indexing and null checks
- [ ] Replace `entryPoints.Where(ep => predicate).ToList()` with direct indexing to create expected sublists
- [ ] Replace `foreach` loops with direct indexed access
- [ ] Replace `entryPoints.Any(ep => predicate)` with direct boolean checks using indices
- [ ] Update assertions to use direct indexing instead of LINQ operations
