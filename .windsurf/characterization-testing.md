🎯 Goal: Automatically Generate Characterization Tests
We want an agent that:

Analyzes the legacy C# code.

Identifies public-facing behavior (methods, classes, services).

Generates tests that exercise the current behavior.

Records expected outputs (snapshots or assertions).

Runs and stores the tests to act as a behavioral safety net.

🧠 Step-by-Step Strategy
1. Target Identification
Use Roslyn to:

Traverse the syntax tree and semantic model.

Identify:

Public classes and methods

Methods with side effects or high complexity

Entrypoints (e.g., controller actions, service interfaces)

Apply heuristics to prioritize:

Methods with many call sites

Classes with high cyclomatic complexity

Code lacking existing tests

2. Dependency Isolation & Seam Injection
Before we can generate tests, we need to make the code testable:

Detect and inject test seams (using interfaces, delegates, or wrapper classes).

Use Microsoft Fakes, Typemock, or Moq for hard dependencies.

Automatically extract interfaces or constructor parameters for key classes.

If the method uses static/global/stateful dependencies:

Wrap them or refactor them behind seams before proceeding.

3. Input Space Exploration
For each method or class:

Use reflection + Roslyn to gather:

Parameter types

Default constructors

Public properties

Automatically generate sample inputs:

Use AutoFixture

Or integrate a generative fuzzer for method parameters

Allow constraints:

Keep values within valid business ranges

Avoid null unless intentionally testing nullability

4. Execution & Output Capture
Generate tests that:

Call the method with the generated inputs

Capture:

Return value

Side effects (e.g., state changes, database calls via mock recording)

Exceptions

Console or logging output (if relevant)

Use snapshot testing:

Serialize output to JSON or string and store in .snap files

On rerun, compare actual output with saved snapshot

5. Test Template Generation
Emit C# tests in the project's framework (xUnit/NUnit/MSTest):

csharp
Copy
Edit
[Fact]
public void Characterization_MyService_DoSomething_Example1()
{
    // Arrange
    var service = new MyService(/* mock deps */);
    var input = new MyInput { /* ... */ };

    // Act
    var result = service.DoSomething(input);

    // Assert
    var snapshot = LoadSnapshot("DoSomething_Example1");
    Assert.Equal(snapshot, Serialize(result));
}
Frameworks:

Use Verify or Snapper for snapshot testing

Optionally generate golden master tests using test case attributes

6. Validation and Maintenance
Mark generated tests as [Category("Characterization")] or [Trait(...)]

Automatically regenerate snapshots if they change and manual approval is given

Create a dashboard to review and approve test coverage and diffs

🧪 Example: Characterizing a Legacy Method
Given this method:
csharp
Copy
Edit
public class LegacyBillingService {
    public Invoice GenerateInvoice(Customer customer, DateTime date) {
        // 200 lines of code, legacy dependencies
    }
}
The system would:
Detect GenerateInvoice as a public method.

Create a test:

Mock Customer using AutoFixture or a factory

Call GenerateInvoice for a few representative dates

Capture result:

Serialize Invoice to JSON

Assert it matches snapshot

Save to file:

Characterization_LegacyBillingService_GenerateInvoice_Test1.cs

With .snap file storing expected result

🔁 Bonus: Iterative Refinement
On future runs, detect changes in behavior

Alert human if refactor changed output

Allow diff review and selective snapshot update