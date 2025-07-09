using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis.MSBuild;

namespace RoslynRefactoring;

public class CsProject(string projectPath, string fileName)
{
    public async Task OpenAndApplyRefactoring(IRefactoring refactoring)
    {
        MSBuildLocator.RegisterDefaults();
        using var workspace = MSBuildWorkspace.Create();
        var project = await workspace.OpenProjectAsync(projectPath);
        var document = project.Documents.FirstOrDefault(d => d.Name == fileName);

        if (document == null)
        {
            Console.WriteLine($"File {fileName} not found in project.");
            return;
        }

        var newDocument = await refactoring.PerformAsync(document);
        var newSolution = document.Project.Solution.WithDocumentSyntaxRoot(
            newDocument.Id,
            (await newDocument.GetSyntaxRootAsync())!
        );

        workspace.TryApplyChanges(newSolution);
    }
}
