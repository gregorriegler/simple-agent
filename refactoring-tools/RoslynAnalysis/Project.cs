using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.MSBuild;

namespace RoslynAnalysis;

public class AnalysisProject
{
    private readonly string _projectPath;
    private readonly string _fileName;

    public AnalysisProject(string projectPath, string fileName)
    {
        _projectPath = projectPath;
        _fileName = fileName;
    }

    public async Task OpenAndApplyAnalysis(IAnalysis analysis)
    {
        using var workspace = MSBuildWorkspace.Create();
        var project = await workspace.OpenProjectAsync(_projectPath);
        
        var result = await analysis.AnalyzeAsync(project, _fileName);
        
        var json = System.Text.Json.JsonSerializer.Serialize(result, new System.Text.Json.JsonSerializerOptions
        {
            WriteIndented = true
        });
        
        Console.WriteLine(json);
    }
}