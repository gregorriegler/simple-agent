using ExtractMethodTool;
using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.MSBuild;

if (args.Length != 5)
{
    Console.WriteLine("Usage: dotnet run -- {projectPath} {fileName} {startLine}:{startColumn} {endLine}:{endColumn} {newMethodName}");
    return;
}

var projectPath = args[0].Trim('"');;
var fileName = args[1];
var startPosition = ParsePosition(args[2]);
var endPosition = ParsePosition(args[3]);
var newMethodName = args[4];

if (startPosition == null || endPosition == null)
{
    Console.WriteLine("Start and end positions must be in the format line:column (e.g., 10:0)");
    return;
}

MSBuildLocator.RegisterDefaults();

using var workspace = MSBuildWorkspace.Create();
var project = await workspace.OpenProjectAsync(projectPath);
var document = project.Documents.FirstOrDefault(d => d.Name == fileName);

if (document == null)
{
    Console.WriteLine($"File {fileName} not found in project.");
    return;
}

var selection = new CodeSelection(
    startPosition.Value.line,
    startPosition.Value.column,
    endPosition.Value.line,
    endPosition.Value.column
);

var newDocument = await ExtractMethod.ExtractAsync(document, newMethodName, selection);
var newSolution = document.Project.Solution.WithDocumentSyntaxRoot(
    newDocument.Id,
    (await newDocument.GetSyntaxRootAsync())!
);
workspace.TryApplyChanges(newSolution);

Console.WriteLine($"✅ Extracted method '{newMethodName}' into {fileName}");

static (int line, int column)? ParsePosition(string input)
{
    var parts = input.Split(':');
    if (parts.Length != 2) return null;

    if (int.TryParse(parts[0], out var line) && int.TryParse(parts[1], out var column))
        return (line, column);

    return null;
}

public record CodeSelection(int StartLine, int StartColumn, int EndLine, int EndColumn);