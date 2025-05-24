using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;

namespace ExtractMethodTool.Tests;

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

        await VerifyExtract(code, "AddOneWithOne", new CodeSelection(6,0,6,19));
    }
    
    [Test]
    public async Task CanExtractSimpleSwitchWithReturn()
    {
        var code = @"
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

        await VerifyExtract(code, "ComputeSpeed", new CodeSelection(8,0,12,10));
    }
    
    [Test]
    public async Task CanExtractVoid()
    {
        var code = @"
public class Console
{
    public void Write()
    {
        Console.WriteLine(""Hello World"");
    }
}";

        await VerifyExtract(code, "Write", new CodeSelection(6,0,6,44));
    }
    
    [Test]
    public async Task CanExtractOnlyAPartThatReturns()
    {
        var code = @"
public class Calculator
{
    public void Plus()
    {
        var a = 1+1;
        var b = a+3;
    }
}";

        await VerifyExtract(code, "AddOneWithOne", new CodeSelection(6,17,6,21));
    }

    private static async Task VerifyExtract(string code, string newMethodName, CodeSelection codeSelection)
    {
        var document = CreateDocument(code);
        var newRoot = await ExtractMethod.ExtractAsync(document, newMethodName, codeSelection); //TBD
        var formatted = Formatter.Format(newRoot, new AdhocWorkspace());
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