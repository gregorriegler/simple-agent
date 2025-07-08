# Goal: Single-Project Cross-File Inline Method Refactoring

## Objective
Extend the existing [`InlineMethod`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:10) refactoring tool to work across multiple files within the same project.

## Current State Analysis
The current [`InlineMethod`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:10) implementation only handles basic same-document scenarios:

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

## Target Scenarios (Cross-File Within Same Project)

### 1. Basic Static Method Across Files
```csharp
// File: Utils/Calculator.cs
namespace MyProject.Utils
{
    public static class Calculator
    {
        public static int Add(int a, int b) => a + b;
    }
}

// File: Services/OrderService.cs - TARGET SCENARIO
using MyProject.Utils;

namespace MyProject.Services
{
    public class OrderService
    {
        public void ProcessOrder()
        {
            var total = Calculator.Add(10, 5); // Should inline to: var total = 10 + 5;
        }
    }
}
```

### 2. Instance Method Across Files
```csharp
// File: Helpers/StringHelper.cs
namespace MyProject.Helpers
{
    public class StringHelper
    {
        public string Reverse(string input) => new string(input.Reverse().ToArray());
    }
}

// File: Controllers/HomeController.cs - TARGET SCENARIO
using MyProject.Helpers;

namespace MyProject.Controllers
{
    public class HomeController
    {
        public void ProcessText()
        {
            var helper = new StringHelper();
            var result = helper.Reverse("hello"); // Should inline method body
        }
    }
}
```

### 3. Method with Dependencies
```csharp
// File: Extensions/StringExtensions.cs
using System.Linq;

namespace MyProject.Extensions
{
    public static class StringExtensions
    {
        public static bool IsEmpty(string value) => string.IsNullOrEmpty(value);
    }
}

// File: Validators/InputValidator.cs - TARGET SCENARIO
using MyProject.Extensions;

namespace MyProject.Validators
{
    public class InputValidator
    {
        public bool Validate(string input)
        {
            return !StringExtensions.IsEmpty(input); // Should inline and preserve using System.Linq if needed
        }
    }
}
```

## Success Criteria
1. **Cross-File Symbol Resolution**: Find method declarations in other files within the same project
2. **Namespace Management**: Handle different namespaces within the same project
3. **Using Statement Analysis**: Preserve or add required using statements after inlining
4. **Type Reference Resolution**: Resolve types used in method bodies across files
5. **Compilation Validation**: Ensure inlined code compiles correctly in target context

## Technical Approach
- Extend [`FindMethodDeclarationAsync()`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:63) to search across all project documents
- Use project-wide semantic model instead of document-specific
- Implement using statement dependency analysis
- Add namespace resolution for inlined method bodies
- Validate accessibility within project scope (public, internal, private)

## Implementation Steps
1. Modify symbol resolution to search project-wide instead of document-only
2. Add using statement analysis and injection logic
3. Implement namespace context handling for inlined code
4. Add type reference resolution across files
5. Create comprehensive test cases for cross-file scenarios

## Scenarios

### Simple Static Method Call - DRAFT
**File Structure:**
- `Utils/MathHelper.cs` - Contains simple static method
- `Services/Calculator.cs` - Calls the static method

**Scenario:** Inline a basic static method call across files with no dependencies.

### Instance Method with Simple Return - DRAFT
**File Structure:**
- `Helpers/TextProcessor.cs` - Contains instance method
- `Controllers/ApiController.cs` - Creates instance and calls method

**Scenario:** Inline an instance method call where method has simple return expression.

### Static Method with Using Statement Dependency - DRAFT
**File Structure:**
- `Extensions/CollectionExtensions.cs` - Uses `System.Linq`
- `Services/DataService.cs` - Calls extension method

**Scenario:** Inline method that requires adding using statement to target file.

### Method with Multiple Parameters and Local Variables - DRAFT
**File Structure:**
- `Processors/StringProcessor.cs` - Method with parameters and local vars
- `Handlers/RequestHandler.cs` - Calls method with arguments

**Scenario:** Inline method with parameter substitution and local variable handling.

### Method Not Found in Project (Exception) - DRAFT
**File Structure:**
- `Services/OrderService.cs` - Calls method that doesn't exist in project

**Scenario:** Should provide clear error when target method cannot be found in any project file.

### Method with Compilation Errors After Inline (Exception) - DRAFT
**File Structure:**
- `Helpers/DataHelper.cs` - Method using types not available in target context
- `Controllers/DataController.cs` - Target file missing required using statements

**Scenario:** Should detect when inlining would cause compilation errors and provide helpful feedback.
