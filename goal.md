# Goal: Cross-Project Inline Method Refactoring

## Objective
Extend the existing [`InlineMethod`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:10) refactoring tool to work across project boundaries within the same solution.

## Current State Analysis
The current [`InlineMethod`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:10) implementation only handles basic single-project scenarios:

**What Currently Works:**
- Simple method calls within the same document
- Basic parameter substitution
- Expression-bodied methods (converted to block syntax)

**Current Single-Project Limitations:**
- Only works within the same document/file
- No cross-file symbol resolution within same project
- No handling of complex dependencies (using statements, type references)
- No generic method support
- No method overload resolution

## Cross-Project Challenges
Extending to cross-project scenarios introduces additional complexity:

### 1. Symbol Resolution Scope
- [`FindMethodDeclarationAsync()`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:63) only searches current document
- Need solution-wide semantic model for cross-project symbol resolution
- Assembly boundary considerations

### 2. Simple Cross-Project Scenarios (Start Here)
**Basic Static Method:**
```csharp
// Project B (MathLibrary)
public static class Calculator
{
    public static int Add(int a, int b) => a + b;
}

// Project A (Consumer) - TARGET SCENARIO
var sum = Calculator.Add(5, 3); // Should inline to: var sum = 5 + 3;
```

**Public Instance Method:**
```csharp
// Project B (Utils)
public class StringHelper
{
    public string Reverse(string input) => new string(input.Reverse().ToArray());
}

// Project A - TARGET SCENARIO
var helper = new StringHelper();
var result = helper.Reverse("hello"); // Should inline method body
```

### 3. Advanced Cross-Project Challenges (Future)
- Namespace/using statement management
- Internal member access validation
- Generic method resolution
- Complex dependency chains

## Success Criteria
1. **Cross-Project Symbol Resolution**: Find and inline methods from referenced projects
2. **Dependency Management**: Automatically add required using statements and references
3. **Visibility Validation**: Prevent inlining of inaccessible members (internal/private)
4. **Compilation Context**: Work with solution-wide semantic models
5. **Namespace Resolution**: Handle type references across project boundaries

## Technical Approach
- Extend semantic model scope to solution-wide context
- Implement cross-project dependency analysis
- Add automatic using statement injection
- Validate member accessibility across assembly boundaries
- Support both library-to-consumer and peer-to-peer project inlining
