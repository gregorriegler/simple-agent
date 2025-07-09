using Microsoft.CodeAnalysis;

namespace RoslynRefactoring.Tests.TestHelpers;

public static class DocumentTestHelper
{
    public static Document CreateDocument(string code)
    {
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        return project.AddDocument("Test.cs", code);
    }

    public static Microsoft.CodeAnalysis.Project CreateWorkspaceWithProject()
    {
        var workspace = new AdhocWorkspace();
        return workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));
    }

    public static Document CreateDocumentInProject(Microsoft.CodeAnalysis.Project project, string fileName, string code)
    {
        return project.AddDocument(fileName, code);
    }

    public static Document CreateTwoDocumentProject(string sourceFileCode, string targetFileCode)
    {
        var project = CreateWorkspaceWithProject();

        // Add both files to the project
        project = CreateDocumentInProject(project, "Utils/MathHelper.cs", sourceFileCode).Project;
        return CreateDocumentInProject(project, "Services/Calculator.cs", targetFileCode);
    }

    public static Solution CreateSolutionWithFiles(params (string fileName, string code)[] files)
    {
        var workspace = new AdhocWorkspace();
        var solution = workspace.CurrentSolution;

        var project = solution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        foreach (var (fileName, code) in files)
        {
            project = project.AddDocument(fileName, code).Project;
        }

        return project.Solution;
    }
}
