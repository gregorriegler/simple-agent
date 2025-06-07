🎯 Definition: What Counts as an "Entry Point"?
In a legacy C# application, entry points typically include:

| Type                                   | Examples                                                           |
| -------------------------------------- | ------------------------------------------------------------------ |
| **Public API surfaces**                | `public` methods in `public` classes, especially in service layers |
| **UI/event handlers**                  | WinForms/WPF event methods, WebForms lifecycle methods             |
| **ASP.NET Controllers**                | `Controller` methods in ASP.NET MVC/WebAPI                         |
| **Main program starts**                | `Program.Main`, worker services, hosted services                   |
| **Scheduled jobs or Windows services** | Anything implementing `IHostedService`, timer callbacks            |
| **Message consumers**                  | Methods handling messages from queues/buses                        |
| **Interfaces**                         | All public interface methods (especially if used via DI)           |


🔍 How to Find Entry Points
✅ Use Roslyn to Analyze the Codebase
We'll write an analyzer that does the following:

1. Enumerate All Public Types and Methods
```csharp
var publicMethods = compilation
    .SyntaxTrees
    .SelectMany(tree => tree.GetRoot().DescendantNodes())
    .OfType<MethodDeclarationSyntax>()
    .Where(method =>
    {
        var symbol = semanticModel.GetDeclaredSymbol(method);
        return symbol.DeclaredAccessibility == Accessibility.Public &&
               symbol.ContainingType.DeclaredAccessibility == Accessibility.Public;
    });
```
This gets all public methods in public classes.

2. Filter by High-Likelihood Entry Points
Apply heuristics:

Controllers
```csharp
// Class inherits from Controller or ControllerBase
symbol.ContainingType.BaseType?.Name.Contains("Controller") == true
```
Service Interfaces
```csharp
// Interface methods injected via DI (constructor injection)

If used in ConfigureServices() or via [Inject], mark all interface methods as entry points
```
Async Jobs or Handlers
Look for:
```csharp
ExecuteAsync()
```

Handle() in MediatR-style handlers
```csharp
Handle()
```

Any method registered to a background task system

Main Method
```csharp
method.Identifier.Text == "Main" &&
method.Modifiers.Any(SyntaxKind.StaticKeyword)
```
3. Call Graph Backtracing (Optional but Powerful)
You can:

Start from Program.Main and trace outward to find all reachable public methods

Prioritize methods not called from within the project (entry point to your internal world)

Use Roslyn’s call graph (or build a simple graph yourself) to:

Mark all "leaf" methods called from outside the project

Exclude utility or helper methods

4. Tagging and Confidence Levels
Assign confidence levels:

✅ High: controller actions, Main, DI service interfaces

⚠️ Medium: public methods with many external references

❌ Low: private/internal methods, or helpers

🧠 Bonus: Heuristic Boosters
Method has many instructions → likely does business logic

Method has side effects (e.g. database, network, file IO)

Method has no unit test coverage → prioritize it!

✅ Output Format for the Agent
Each discovered entry point should be tagged with:

```json
{
  "type": "EntryPoint",
  "name": "GenerateInvoice",
  "declaringType": "LegacyBillingService",
  "file": "Services/LegacyBillingService.cs",
  "signature": "Invoice GenerateInvoice(Customer customer, DateTime date)",
  "confidence": "high"
}
```