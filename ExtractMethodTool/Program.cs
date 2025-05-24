using System.Text.Json;
using ExtractMethodTool;
using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis.MSBuild;

if (args.Length != 1)
{
    Console.WriteLine("Usage: dotnet run -- path/to/arguments.json");
    return;
}

MSBuildLocator.RegisterDefaults();

var argumentsJson = await File.ReadAllTextAsync(args[0]);
var options = new JsonSerializerOptions
{
    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
};
var arguments = JsonSerializer.Deserialize<Arguments>(argumentsJson, options)!;

using var workspace = MSBuildWorkspace.Create();
var project = await workspace.OpenProjectAsync(arguments.ProjectPath);
var document = project.Documents.FirstOrDefault(d => d.Name == arguments.FileName);

if (document == null)
{
    Console.WriteLine($"File {arguments.FileName} not found in project.");
    return;
}

var newRoot = await ExtractMethod.RewriteAsync(document, arguments.NewMethodName, arguments.Selection);
var updatedDoc = document.WithSyntaxRoot(newRoot);
var newText = await updatedDoc.GetTextAsync();

await File.WriteAllTextAsync(document.FilePath!, newText.ToString());

Console.WriteLine($"✅ Extracted method '{arguments.NewMethodName}' into {arguments.FileName}");