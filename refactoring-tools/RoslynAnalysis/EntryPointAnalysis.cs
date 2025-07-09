namespace RoslynAnalysis;

/// <summary>
/// Analyzes the C# project to find the best entry points for characterization tests
/// </summary>
public class EntryPointAnalysis : IAnalysis
{
    public EntryPointAnalysis()
    {
    }

    public static EntryPointAnalysis Create(string[] args)
    {
        return new EntryPointAnalysis();
    }

    public async Task<object> AnalyzeAsync(Microsoft.CodeAnalysis.Project project, string fileName)
    {
        var entryPointFinder = new EntryPointFinder();
        var entryPoints = await entryPointFinder.FindEntryPointsAsync(project.FilePath!);

        return new
        {
            project = project.Name,
            fileName = fileName,
            entryPoints = entryPoints
        };
    }
}
