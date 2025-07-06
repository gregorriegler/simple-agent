using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.MSBuild;

namespace RoslynAnalysis;

public class AnalysisProject
{
    private readonly string _projectPath;
    private readonly string _fileName;

    public AnalysisProject(string projectPath, string fileName)
    {
        _projectPath = ResolveProjectPath(projectPath);
        _fileName = fileName;
    }

    private static string ResolveProjectPath(string path)
    {
        // If it's already a file, return as-is
        if (File.Exists(path))
        {
            return path;
        }

        // If it's a directory, find the appropriate project file
        if (Directory.Exists(path))
        {
            // First look for .sln files (higher priority)
            var slnFiles = Directory.GetFiles(path, "*.sln");
            if (slnFiles.Length > 0)
            {
                return slnFiles[0];
            }

            // Then look for .csproj files
            var csprojFiles = Directory.GetFiles(path, "*.csproj");
            if (csprojFiles.Length > 0)
            {
                return csprojFiles[0];
            }

            throw new FileNotFoundException($"No .sln or .csproj files found in directory: '{path}'");
        }

        // If neither file nor directory exists, throw original error
        throw new FileNotFoundException($"Project file not found: '{path}'");
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
