using System.Text.Json;
using ExtractMethodTool;
using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis.MSBuild;
using Microsoft.CodeAnalysis.Text;

if (args.Length != 1)
{
    Console.WriteLine("Usage: dotnet run -- path/to/plan.json");
    return;
}

MSBuildLocator.RegisterDefaults();

var planJson = await File.ReadAllTextAsync(args[0]);
var plan = JsonSerializer.Deserialize<RefactorPlan>(planJson)!;

using var workspace = MSBuildWorkspace.Create();
var project = await workspace.OpenProjectAsync(plan.ProjectPath);
var document = project.Documents.FirstOrDefault(d => d.Name == plan.FileName);

if (document == null)
{
    Console.WriteLine($"File {plan.FileName} not found in project.");
    return;
}

var text = await document.GetTextAsync();
var lines = text.Lines;
int GetPos(int line, int col) => lines[line - 1].Start + col - 1;

var span = TextSpan.FromBounds(
    GetPos(plan.Selection.StartLine, plan.Selection.StartColumn),
    GetPos(plan.Selection.EndLine, plan.Selection.EndColumn)
);

var newRoot = await ExtractMethod.RewriteAsync(document, span, plan.NewMethodName);
var updatedDoc = document.WithSyntaxRoot(newRoot);
var newText = await updatedDoc.GetTextAsync();

await File.WriteAllTextAsync(document.FilePath!, newText.ToString());

Console.WriteLine($"✅ Extracted method '{plan.NewMethodName}' into {plan.FileName}");