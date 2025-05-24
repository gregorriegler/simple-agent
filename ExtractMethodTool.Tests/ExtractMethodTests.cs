using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;

namespace ExtractMethodTool.Tests;

[TestFixture]
public class ExtractMethodTests
{
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