using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.MSBuild;
using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace RoslynAnalysis;

public class MSBuildWorkspaceLoader : IWorkspaceLoader
{
    static MSBuildWorkspaceLoader()
    {
        try
        {
            MSBuildLocator.RegisterDefaults();
        }
        catch (InvalidOperationException)
        {
        }
    }
    
    public async Task<IEnumerable<Microsoft.CodeAnalysis.Project>> LoadProjectsAsync(string projectPath)
    {
        using var workspace = MSBuildWorkspace.Create();
        
        if (Path.GetExtension(projectPath).Equals(".sln", StringComparison.OrdinalIgnoreCase))
        {
            var solution = await workspace.OpenSolutionAsync(projectPath);
            
            return solution.Projects.ToList();
        }
        else
        {
            var project = await workspace.OpenProjectAsync(projectPath);
                
            return new[] { project };
        }
    }
}
