# Refactoring Plan

## Identified Issues to Improve

### 1. Long Method - EntryPointFinder.FindEntryPointsAsync()
The [`EntryPointFinder.FindEntryPointsAsync()`](refactoring-tools/RoslynAnalysis/EntryPointFinder.cs:16) method is 80 lines long and handles multiple responsibilities:
- Project loading and document collection
- Method discovery and symbol analysis
- Entry point creation and validation
- Call graph analysis
- Reachability calculation
- Result sorting and filtering

### 2. Long Method - EntryPointFinder.CalculateReachableMethodsCount()
The [`EntryPointFinder.CalculateReachableMethodsCount()`](refactoring-tools/RoslynAnalysis/EntryPointFinder.cs:137) method is 71 lines long and handles:
- Method traversal queue management
- Symbol resolution and name generation
- Invocation expression analysis
- Fallback method name resolution
- Recursive method discovery

### 3. Duplicated Code - Fully Qualified Name Generation
The pattern for generating fully qualified method names appears 4 times:
- Line 44: `$"{methodSymbol.ContainingType.ContainingNamespace.ToDisplayString()}.{methodSymbol.ContainingType.Name}.{methodSymbol.Name}"`
- Line 68: `$"{calledMethodSymbol.ContainingType.ContainingNamespace.ToDisplayString()}.{calledMethodSymbol.ContainingType.Name}.{calledMethodSymbol.Name}"`
- Line 154: `$"{currentMethodSymbol.ContainingType.ContainingNamespace.ToDisplayString()}.{currentMethodSymbol.ContainingType.Name}.{currentMethodSymbol.Name}"`
- Line 173: `$"{calledMethodSymbol.ContainingType.ContainingNamespace.ToDisplayString()}.{calledMethodSymbol.ContainingType.Name}.{calledMethodSymbol.Name}"`

### 4. Long Parameter List - CalculateReachableMethodsCount()
The [`CalculateReachableMethodsCount()`](refactoring-tools/RoslynAnalysis/EntryPointFinder.cs:137) method has a long parameter with complex tuple type that makes the signature hard to read.

### 5. Magic Numbers and Hardcoded Values
- Line 133: Hardcoded initial reachable count of `1`
- Lines 224-230: Hardcoded test attribute names array

## Refactoring Tasks

- [x] Extract method: Create `GetFullyQualifiedMethodName(IMethodSymbol)` to eliminate duplication
- [x] Extract method: Create `CollectAllMethods()` from FindEntryPointsAsync to handle method discovery
- [ ] Extract method: Create `CollectPublicEntryPoints()` from FindEntryPointsAsync to handle entry point creation
- [x] Extract method: Create `AnalyzeMethodCalls()` from FindEntryPointsAsync to handle call graph analysis
- [x] Extract method: Create `FilterUncalledEntryPoints()` from FindEntryPointsAsync to handle filtering
- [x] Extract method: Create `ProcessMethodInvocations()` from CalculateReachableMethodsCount to handle invocation analysis
- [x] Extract method: Create `ResolveMethodSymbol()` from CalculateReachableMethodsCount to handle symbol resolution
- [x] Extract constant: Create `DEFAULT_REACHABLE_COUNT` constant for the initial reachable count
- [x] Extract constant: Create `TEST_ATTRIBUTES` constant for test attribute names
- [x] Introduce parameter object: Create `MethodInfo` class to replace complex tuple parameter
