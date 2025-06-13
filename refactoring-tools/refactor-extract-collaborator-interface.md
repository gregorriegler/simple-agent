📝 **Goal:**
Create a C# refactoring tool (likely as a Roslyn-based analyzer/code fix or standalone command) that, when invoked on a class that depends on a "collaborator" (i.e., another concrete class), automatically:

* Extracts an interface from the collaborator class, containing the members used by the dependent class.
* Injects the interface (via constructor or property injection) instead of the concrete collaborator.
* Updates usages in the dependent class to reference the interface, not the concrete type.
* The refactoring should implement the `IRefactoring` interface:

```csharp
public interface IRefactoring
{
    Task<Document> PerformAsync(Document document);
}
```
* The CodeSelection of the collaborator should be passed via constructor or factory

---

## 2. Component Diagram (Rough, Mermaid)

```mermaid
flowchart TD
    subgraph RefactoringTool
        A[Entry: PerformAsync(Document)]
        B[Analyzer: Find Collaborator Usage]
        C[InterfaceExtractor: Generate Interface]
        D[Injector: Change Dependency to Interface]
        E[Rewriter: Update Usages]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E --> A
```

---

## 3. List of Scenarios (Ordered by Simplicity)

1. **Simple Collaborator:**

   * A class `OrderService` directly uses `PaymentProcessor` (single method called).
   * Tool extracts `IPaymentProcessor` with that method and injects it.

2. **Multiple Methods Used:**

   * Dependent class uses several public methods of the collaborator.
   * Tool includes all used methods in the interface.

3. **Collaborator Already Has Interface:**

   * Collaborator already implements an interface.
   * Tool detects and uses the existing interface, or merges needed members.

4. **Property Injection:**

   * Dependent class gets collaborator via property.
   * Tool injects the interface as a property.

5. **Constructor with Multiple Dependencies:**

   * Class already has other injected dependencies.
   * Tool updates the constructor signature accordingly.

6. **Multiple Collaborators:**

   * Several collaborator types are used.
   * Tool can extract interfaces and inject multiple dependencies.

7. **Cross-Project Types:**

   * Collaborator is in another project/assembly.
   * Tool must handle interface placement and references.

---

## 4. Refining Scenario 1: Simple Collaborator

### Examples (Zero/One/Many)

**Zero**

- [ ] A class that does not use any collaborator at all.

  * Example: `OrderService` does everything itself, no other class involved.

**One**

- [ ] A class that uses one collaborator and only calls one method on it.

  * Example: `OrderService` creates a `PaymentProcessor` and calls `ProcessPayment()`.
- [ ] A class that uses one collaborator and calls one property on it.

  * Example: `OrderService` creates a `PaymentProcessor` and reads the `Status` property.

**Many**

- [ ] A class that uses one collaborator and calls multiple methods or properties on it.

  * Example: `OrderService` creates a `PaymentProcessor`, calls `ProcessPayment()`, and checks `Status`.
- [ ] A class that uses many collaborators, but only one is a candidate for extraction (focus on just one for now).

  * Example: `OrderService` uses both `PaymentProcessor` and `Logger`, but the refactoring is triggered for `PaymentProcessor` only.

