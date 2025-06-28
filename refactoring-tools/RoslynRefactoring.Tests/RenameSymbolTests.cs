using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class RenameSymbolTests
{
    [Test]
    public async Task CanRenameUnusedLocalVariable()
    {
        var code = @"
public class Test
{
    public void Method()
    {
        int unused = 5;
        Console.WriteLine(""Hello"");
    }
}";

        await VerifyRename(code, Cursor.Parse("6:13"), "temp");
    }

    [Test]
    public async Task CanRenameVariableWithOneUsage()
    {
        var code = @"
public class Test
{
    public void Method()
    {
        int count = 0;
        return count;
    }
}";

        await VerifyRename(code, Cursor.Parse("6:13"), "total");
    }

    [Test]
    public async Task CanRenameVariableWithManyUsages()
    {
        var code = @"
public class Test
{
    public void Method()
    {
        int value = 10;
        int result = value + value * 2;
        Console.WriteLine(value);
        return result + value;
    }
}";

        await VerifyRename(code, Cursor.Parse("6:13"), "number");
    }

    [Test]
    public async Task CanRenameVariableInDifferentScopes()
    {
        var code = @"
public class Test
{
    public void Method()
    {
        int value = 10;
        {
            int value = 20; // inner scope variable
            Console.WriteLine(value);
        }
        Console.WriteLine(value); // outer scope variable
    }
}";

        await VerifyRename(code, Cursor.Parse("8:17"), "innerValue");
    }

    [Test]
    public async Task CanRenameVariableInLoop()
    {
        var code = @"
public class Test
{
    public void Method()
    {
        for(int i = 0; i < 10; i++)
        {
            Console.WriteLine(i);
        }
    }
}";

        await VerifyRename(code, Cursor.Parse("6:17"), "index");
    }

    [Test]
    public async Task CanRenameUnusedPrivateMethod()
    {
        var code = @"
public class Test
{
    private void DoSomething()
    {
        Console.WriteLine(""Hello"");
    }
    
    public void Main()
    {
        Console.WriteLine(""Main method"");
    }
}";

        await VerifyRename(code, Cursor.Parse("4:18"), "ProcessData");
    }

    [Test]
    public async Task CanRenamePrivateMethodWithOneUsage()
    {
        var code = @"
public class Test
{
    private void DoSomething()
    {
        Console.WriteLine(""Hello"");
    }
    
    public void Main()
    {
        DoSomething();
    }
}";

        await VerifyRename(code, Cursor.Parse("4:18"), "ProcessData");
    }

    private static async Task VerifyRename(string code, Cursor cursor, string newName)
    {
        var document = CreateDocument(code);
        var renameSymbol = new RenameSymbol(cursor, newName);
        var updatedDocument = await renameSymbol.PerformAsync(document);
        var formatted = Formatter.Format((await updatedDocument.GetSyntaxRootAsync())!, new AdhocWorkspace());
        await Verify(formatted.ToFullString());
    }

    private static Document CreateDocument(string code)
    {
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        return project.AddDocument("Test.cs", code);
    }
}