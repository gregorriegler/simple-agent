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
                // Parse the solution file to extract the first .csproj file
                var csprojFromSolution = ExtractFirstCsprojFromSolution(slnFiles[0]);
                if (csprojFromSolution != null)
                {
                    return csprojFromSolution;
                }
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

    private static string? ExtractFirstCsprojFromSolution(string solutionPath)
    {
        try
        {
            var solutionDir = Path.GetDirectoryName(solutionPath)!;
            var lines = File.ReadAllLines(solutionPath);

            foreach (var line in lines)
            {
                // Look for project lines in the format:
                // Project("{GUID}") = "ProjectName", "ProjectPath.csproj", "{GUID}"
                if (line.StartsWith("Project(") && line.Contains(".csproj"))
                {
                    var parts = line.Split(',');
                    if (parts.Length >= 2)
                    {
                        // Extract the project path (second part, between quotes)
                        var projectPathPart = parts[1].Trim();
                        if (projectPathPart.StartsWith("\"") && projectPathPart.EndsWith("\""))
                        {
                            var relativePath = projectPathPart.Substring(1, projectPathPart.Length - 2);
                            var fullPath = Path.Combine(solutionDir, relativePath);

                            if (File.Exists(fullPath))
                            {
                                return fullPath;
                            }
                        }
                    }
                }
            }
        }
        catch
        {
            // If parsing fails, return null to fall back to .csproj search
        }

        return null;
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
