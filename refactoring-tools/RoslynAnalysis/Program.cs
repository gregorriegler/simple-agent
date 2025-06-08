using System.CommandLine;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace RoslynAnalysis;

public class Program
{
    public static async Task<int> Main(string[] args)
    {
        var rootCommand = new RootCommand("Entry Point Finder for Characterization Testing");
        
        var projectPathOption = new Option<string>(
            name: "--project-path",
            description: "Path to the C# project file (.csproj) or solution file (.sln)"
        )
        {
            IsRequired = true
        };
        
        var outputFileOption = new Option<string?>(
            name: "--output-file",
            description: "Path to the output file (if not specified, output will be written to console)"
        );
        
        rootCommand.AddOption(projectPathOption);
        rootCommand.AddOption(outputFileOption);
        
        rootCommand.SetHandler(async (string projectPath, string? outputFile) =>
        {
            try
            {
                Console.WriteLine($"Analyzing project: {projectPath}");
                
                var workspaceLoader = new MSBuildWorkspaceLoader();
                var entryPointFinder = new EntryPointFinder(workspaceLoader);
                var entryPoints = await entryPointFinder.FindEntryPointsAsync(projectPath);
                
                Console.WriteLine($"Found {entryPoints.Count} entry points.");
                
                var jsonOptions = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    DefaultIgnoreCondition = JsonIgnoreCondition.Never
                };
                
                var json = JsonSerializer.Serialize(entryPoints, jsonOptions);
                
                if (string.IsNullOrEmpty(outputFile))
                {
                    Console.WriteLine(json);
                }
                else
                {
                    await File.WriteAllTextAsync(outputFile, json);
                    Console.WriteLine($"Results written to: {outputFile}");
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error: {ex.Message}");
                Console.Error.WriteLine(ex.StackTrace);
            }
        }, projectPathOption, outputFileOption);
        
        return await rootCommand.InvokeAsync(args);
    }
}
