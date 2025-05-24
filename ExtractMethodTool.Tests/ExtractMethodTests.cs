using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;
using ExtractMethodTool;
using Microsoft.CodeAnalysis.CSharp.Syntax;

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
            case 1: return 20;
            default: throw new ArgumentOutOfRangeException();
        }
    }
}";

        var document = CreateDocument(code);

        // manually locate span of the switch block
        var root = await document.GetSyntaxRootAsync();
        var switchNode = root.DescendantNodes().OfType<SwitchStatementSyntax>().First();
        var span = switchNode.Span;

        var newRoot = await ExtractMethod.RewriteAsync(document, span, "ComputeSpeed");
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