using Microsoft.CodeAnalysis;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class RenameSymbolErrorHandlingTests
{
    [Test]
    public void ShouldReturnMeaningfulErrorWhenCursorIsOnWhitespace()
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
        
        using var consoleOutput = new StringWriter();
        Console.SetOut(consoleOutput);
        
        var result = renameSymbol.PerformAsync(document).Result;
        
        Assert.That(result, Is.EqualTo(document));
        
        var output = consoleOutput.ToString();
        Assert.That(output, Does.Contain("Error: No renameable symbol found at cursor location"));
    }

    [Test]
    public void ShouldReturnMeaningfulErrorWhenCursorIsOnUnsupportedSymbolType()
    {
        var code = @"
public class Test
{
    public string Name { get; set; }
}";

        var document = CreateDocument(code);
        var renameSymbol = new RenameSymbol(Cursor.Parse("4:19"), "NewName"); // cursor on property name
        
        using var consoleOutput = new StringWriter();
        Console.SetOut(consoleOutput);
        
        var result = renameSymbol.PerformAsync(document).Result;
        
        Assert.That(result, Is.EqualTo(document));
        
        var output = consoleOutput.ToString();
        Assert.That(output, Does.Contain("Error: No renameable symbol found at cursor location"));
    }

    private static Document CreateDocument(string code)
    {
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        return project.AddDocument("Test.cs", code);
    }
}