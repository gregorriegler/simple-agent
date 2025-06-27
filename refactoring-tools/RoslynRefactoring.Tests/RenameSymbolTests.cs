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