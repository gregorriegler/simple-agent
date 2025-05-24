using System.Text.Json;
using ExtractMethodTool;
using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis.MSBuild;

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

var newRoot = await ExtractMethod.RewriteAsync(document, plan.NewMethodName, plan.Selection);
var updatedDoc = document.WithSyntaxRoot(newRoot);
var newText = await updatedDoc.GetTextAsync();

await File.WriteAllTextAsync(document.FilePath!, newText.ToString());

Console.WriteLine($"✅ Extracted method '{plan.NewMethodName}' into {plan.FileName}");