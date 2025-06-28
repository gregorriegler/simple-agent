using Microsoft.CodeAnalysis;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class RenameSymbolErrorHandlingTests
{
    [Test]
    public void ShouldThrowErrorWhenCursorIsOnWhitespace()
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
        
        var exception = Assert.ThrowsAsync<InvalidOperationException>(
            async () => await renameSymbol.PerformAsync(document));
        
        Assert.That(exception.Message, Does.Contain("No renameable symbol found at cursor location"));
    }

    [Test]
    public void ShouldProvideHelpfulErrorWhenCursorIsOnUnsupportedSymbolType()
    {
        var code = @"
public class Test
{
    public string Name { get; set; }
}";

        var document = CreateDocument(code);
        var renameSymbol = new RenameSymbol(Cursor.Parse("4:19"), "NewName"); // cursor on property name
        
        var exception = Assert.ThrowsAsync<InvalidOperationException>(
            async () => await renameSymbol.PerformAsync(document));
        
        Assert.That(exception.Message, Does.Contain("Supported symbol types: variables, methods"));
    }

    private static Document CreateDocument(string code)
    {
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        return project.AddDocument("Test.cs", code);
    }
}