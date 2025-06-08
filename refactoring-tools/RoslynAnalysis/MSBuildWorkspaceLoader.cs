using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.MSBuild;
using System;
using System.IO;
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
    
    public async Task<Project?> LoadProjectAsync(string projectPath)
    {
        if (string.IsNullOrWhiteSpace(projectPath))
            throw new ArgumentException("Project path cannot be null or empty", nameof(projectPath));
            
        if (!File.Exists(projectPath))
            throw new FileNotFoundException($"Project file not found: {projectPath}", projectPath);
            
        using var workspace = MSBuildWorkspace.Create();
        
        var project = await workspace.OpenProjectAsync(projectPath);
        
        if (project == null)
            throw new InvalidOperationException($"Failed to load project: {projectPath}");
            
        return project;
    }
}
