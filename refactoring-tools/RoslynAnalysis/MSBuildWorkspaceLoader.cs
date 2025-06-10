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
            // MSBuild is already registered, ignore
        }
    }
    
    public async Task<IEnumerable<Project>> LoadProjectsAsync(string projectPath)
    {
        using var workspace = MSBuildWorkspace.Create();
        
        // Check if it's a solution file
        if (Path.GetExtension(projectPath).Equals(".sln", StringComparison.OrdinalIgnoreCase))
        {
            var solution = await workspace.OpenSolutionAsync(projectPath);
            
            // Return all projects from the solution
            return solution.Projects.ToList();
        }
        else
        {
            // Handle single project file
            var project = await workspace.OpenProjectAsync(projectPath);
                
            return new[] { project };
        }
    }
}
