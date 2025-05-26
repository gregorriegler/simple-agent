using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;

namespace ExtractMethodTool.Tests;

[TestFixture]
public class InlineMethodTests
{
    
    [Test]
    public async Task CanInlineSimple()
    {
        var code = @"
public class Calculator
{
    public int Plus()
    {
        return AddOneWithOne();
    }

    private int AddOneWithOne()
    {
        return 1 + 1;
    }
}";

        await VerifyInline(code, 6,16);
    }
    
    private static async Task VerifyInline(string code, int line, int column)
    {
        var document = CreateDocument(code);
        var updatedDocument = await InlineMethod.InlineMethodAsync(document, line, column);
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