using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;
using RoslynRefactoring.Tests.TestHelpers;
using RoslynRefactoring;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class MoveMemberUpTests
{
    [Test]
    public async Task CanMoveMethodWithZeroDependencies()
    {
        var code = @"
public class Animal
{
    public string Name { get; set; }
}

public class Dog : Animal
{
    public void DoNothing() { }
}";

        await VerifyMoveMemberUp(code, "Dog", "DoNothing");
    }

    private static async Task VerifyMoveMemberUp(string code, string derivedClassName, string memberName)
    {
        var document = DocumentTestHelper.CreateDocument(code);
        var moveMemberUp = new MoveMemberUp(derivedClassName, memberName);
        var updatedDocument = await moveMemberUp.PerformAsync(document);
        var formatted = Formatter.Format((await updatedDocument.GetSyntaxRootAsync())!, new AdhocWorkspace());
        await Verify(formatted.ToFullString());
    }
}
