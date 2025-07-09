using Microsoft.CodeAnalysis;

namespace RoslynRefactoring.Tests.TestHelpers;

public static class DocumentTestHelper
{
    public static Document CreateDocument(string code)
    {
        var projectName = $"TestProject_{Guid.NewGuid():N}";
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject(projectName, $"{projectName}.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        return project.AddDocument("Test.cs", code);
    }

    public static Solution CreateSolutionWithFiles(params (string fileName, string code)[] files)
    {
        var projectName = $"TestProject_{Guid.NewGuid():N}";
        var workspace = new AdhocWorkspace();
        var solution = workspace.CurrentSolution;

        var project = solution.AddProject(projectName, $"{projectName}.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        foreach (var (fileName, code) in files)
        {
            project = project.AddDocument(fileName, code).Project;
        }

        return project.Solution;
    }

    public static (Workspace, Project) CreateWorkspaceWithProject()
    {
        var projectName = $"TestProject_{Guid.NewGuid():N}";
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject(projectName, $"{projectName}.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));
        return (workspace, project);
    }
}
