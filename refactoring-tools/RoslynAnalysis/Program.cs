using Microsoft.Build.Locator;
using RoslynAnalysis;

if (args.Length == 0)
{
    Console.WriteLine("Usage: RoslynAnalysis <analysis-name> <project-path> [file-name] [analysis-args...]");
    Console.WriteLine("       RoslynAnalysis --list-tools");
    return;
}

var analysisName = args[0];

if (analysisName == "--list-tools")
{
    var allAnalyses = AnalysisInfoGenerator.GetAllAnalysisInfo();
    var json = System.Text.Json.JsonSerializer.Serialize(allAnalyses, new System.Text.Json.JsonSerializerOptions
    {
        WriteIndented = true
    });
    Console.WriteLine(json);
    return;
}

if (args.Length < 2)
{
    Console.WriteLine("Error: Project path is required");
    Console.WriteLine("Usage: RoslynAnalysis <analysis-name> <project-path> [file-name] [analysis-args...]");
    return;
}
MSBuildLocator.RegisterDefaults();

var projectPath = args[1].Trim('"');
var fileName = args.Length > 2 ? args[2] : "";
var analysisArgs = args.Skip(3).ToArray();
var analysis = AnalysisInfoGenerator.CreateAnalysis(analysisName, analysisArgs);

var project = new AnalysisProject(projectPath, fileName);

await project.OpenAndApplyAnalysis(analysis);
