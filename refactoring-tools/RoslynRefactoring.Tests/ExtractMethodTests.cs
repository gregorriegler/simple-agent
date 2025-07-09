using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;
using RoslynRefactoring.Tests.TestHelpers;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class ExtractMethodTests
{
    [Test]
    public async Task CanExtractReturn()
    {
        var code = @"
public class Calculator
{
    public int Plus()
    {
        return 1+1;
    }
}";

        await VerifyExtract(code, CodeSelection.Parse("6:0-6:19"), "AddOneWithOne");
    }

    [Test]
    public async Task CanExtractSimpleSwitchWithReturn()
    {
        const string code = @"
public class Bird
{
    private int kind;

    public int GetSpeed()
    {
        switch (kind)
        {
            case 0: return 10;
            default: throw new ArgumentOutOfRangeException();
        }
    }
}";

        await VerifyExtract(code, CodeSelection.Parse("8:0-12:10"), "ComputeSpeed");
    }

    [Test]
    public async Task CanExtractVoid()
    {
        const string code = @"
public class Console
{
    public void Write()
    {
        Console.WriteLine(""Hello World"");
    }
}";

        await VerifyExtract(code, CodeSelection.Parse("6:0-6:44"), "Write");
    }

    [Test]
    public async Task CanExtractOnlyAPartThatReturns()
    {
        const string code = @"
public class Calculator
{
    public void Plus()
    {
        var a = 1+1;
        var b = a+3;
    }
}";

        await VerifyExtract(code, CodeSelection.Parse("6:17-6:21"), "AddOneWithOne");
    }

    [Test]
    public async Task CanExtractSwitchBodyWithReturn()
    {
        const string code = @"
public class Bird
{
    private int kind;

    public int GetSpeed()
    {
        switch (kind)
        {
            case 0: return 10;
            default: throw new ArgumentOutOfRangeException();
        }
    }
}";

        await VerifyExtract(code, CodeSelection.Parse("10:21-10:31"), "Ten");
    }


    private static async Task VerifyExtract(string code, CodeSelection codeSelection, string newMethodName)
    {
        var document = DocumentTestHelper.CreateDocument(code);
        var extractMethod = new ExtractMethod(codeSelection, newMethodName);
        var updatedDocument = await extractMethod.PerformAsync(document);
        var formatted = Formatter.Format((await updatedDocument.GetSyntaxRootAsync())!, new AdhocWorkspace());
        await Verify(formatted.ToFullString());
    }
}
