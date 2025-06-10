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
        if (string.IsNullOrWhiteSpace(projectPath))
            throw new ArgumentException("Project path cannot be null or empty", nameof(projectPath));
            
        if (!File.Exists(projectPath))
            throw new FileNotFoundException($"Project file not found: {projectPath}", projectPath);
            
        using var workspace = MSBuildWorkspace.Create();
        
        // Check if it's a solution file
        if (Path.GetExtension(projectPath).Equals(".sln", StringComparison.OrdinalIgnoreCase))
        {
            var solution = await workspace.OpenSolutionAsync(projectPath);
            
            if (solution == null)
                throw new InvalidOperationException($"Failed to load solution: {projectPath}");
            
            // Return all projects from the solution
            return solution.Projects.ToList();
        }
        else
        {
            // Handle single project file
            var project = await workspace.OpenProjectAsync(projectPath);
            
            if (project == null)
                throw new InvalidOperationException($"Failed to load project: {projectPath}");
                
            return new[] { project };
        }
    }
}
