using Microsoft.CodeAnalysis;
using RoslynRefactoring.Tests.TestHelpers;

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

        var document = DocumentTestHelper.CreateDocument(code);
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

        var document = DocumentTestHelper.CreateDocument(code);
        var renameSymbol = new RenameSymbol(Cursor.Parse("4:19"), "NewName"); // cursor on property name

        AssertMeaningfulErrorResponse(document, renameSymbol);
    }

    private static void AssertMeaningfulErrorResponse(Document document, RenameSymbol renameSymbol)
    {
        using var consoleOutput = new StringWriter();
        Console.SetOut(consoleOutput);

        var result = renameSymbol.PerformAsync(document).Result;

        Assert.That(result, Is.EqualTo(document));

        var output = consoleOutput.ToString();
        Assert.That(output, Does.Contain("Error: No renameable symbol found at cursor location"));
        Assert.That(output, Does.Contain("Supported symbol types: variables, methods"));
    }

}
