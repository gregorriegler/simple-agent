using Microsoft.CodeAnalysis;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class RenameSymbolMeaningfulErrorTests
{
    [Test]
    public void ShouldReturnMeaningfulErrorResponseWhenCursorIsOnWhitespace()
    {
        var code = @"
public class Test
{
    public void Method()
    {
        int value = 10;
    }
}";

        var document = CreateDocument(code);
        var renameSymbol = new RenameSymbol(Cursor.Parse("5:1"), "newName"); // cursor on whitespace
        
        AssertMeaningfulErrorResponse(document, renameSymbol);
    }

    [Test]
    public void ShouldReturnMeaningfulErrorResponseWhenCursorIsOnUnsupportedSymbolType()
    {
        var code = @"
public class Test
{
    public string Name { get; set; }
}";

        var document = CreateDocument(code);
        var renameSymbol = new RenameSymbol(Cursor.Parse("4:19"), "NewName"); // cursor on property name
        
        AssertMeaningfulErrorResponse(document, renameSymbol);
    }

    private static void AssertMeaningfulErrorResponse(Document document, RenameSymbol renameSymbol)
    {
        // Capture console output
        using var consoleOutput = new StringWriter();
        Console.SetOut(consoleOutput);
        
        // Should not throw exception, but should write error to console and return original document
        var result = renameSymbol.PerformAsync(document).Result;
        
        // Should return original document unchanged
        Assert.That(result, Is.EqualTo(document));
        
        // Should write meaningful error message to console
        var output = consoleOutput.ToString();
        Assert.That(output, Does.Contain("Error: No renameable symbol found at cursor location"));
        Assert.That(output, Does.Contain("Supported symbol types: variables, methods"));
    }

    private static Document CreateDocument(string code)
    {
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        return project.AddDocument("Test.cs", code);
    }
}