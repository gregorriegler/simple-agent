namespace RoslynAnalysis;

/// <summary>
/// Analyzes the C# project to find the best entry points for characterization tests
/// </summary>
public class EntryPointAnalysis : IAnalysis
{
    private readonly IWorkspaceLoader _workspaceLoader;

    public EntryPointAnalysis(IWorkspaceLoader workspaceLoader)
    {
        _workspaceLoader = workspaceLoader;
    }

    public static EntryPointAnalysis Create(string[] args)
    {
        return new EntryPointAnalysis(new MSBuildWorkspaceLoader());
    }

    public async Task<object> AnalyzeAsync(Microsoft.CodeAnalysis.Project project, string fileName)
    {
        var entryPointFinder = new EntryPointFinder(_workspaceLoader);
        var entryPoints = await entryPointFinder.FindEntryPointsAsync(project.FilePath!);
        
        return new
        {
            project = project.Name,
            fileName = fileName,
            entryPoints = entryPoints
        };
    }
}