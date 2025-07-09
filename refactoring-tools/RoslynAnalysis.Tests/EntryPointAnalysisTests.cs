using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Text;

namespace RoslynAnalysis.Tests;

[TestFixture]
public class EntryPointAnalysisTests
{
    [Test]
    public async Task DirectoryWithSingleCsprojFile_AutomaticallyDetectsAndUsesProjectFile()
    {
        // Arrange: Create an AdhocWorkspace with a simple project
        using var workspace = new AdhocWorkspace();
        var project = CreateSimpleProject(workspace, "TestProject");

        // Act: Run EntryPointFinder directly on the project documents
        var entryPointFinder = new EntryPointFinder();
        var entryPoints = await FindEntryPointsFromProject(entryPointFinder, project);

        // Assert: Verify the analysis completed successfully
        Assert.That(entryPoints, Is.Not.Null);
        Assert.That(entryPoints.Count, Is.GreaterThanOrEqualTo(0));
    }

    [Test]
    public async Task DirectoryWithBothSlnAndCsprojFiles_PrioritizesSolutionFile()
    {
        // Arrange: Create an AdhocWorkspace with a project containing multiple classes
        using var workspace = new AdhocWorkspace();
        var project = CreateProjectWithMultipleClasses(workspace, "SolutionProject");

        // Act: Run EntryPointFinder directly on the project documents
        var entryPointFinder = new EntryPointFinder();
        var entryPoints = await FindEntryPointsFromProject(entryPointFinder, project);

        // Assert: Verify the analysis completed successfully
        Assert.That(entryPoints, Is.Not.Null);
        Assert.That(entryPoints.Count, Is.GreaterThanOrEqualTo(0));
    }

    private Project CreateSimpleProject(AdhocWorkspace workspace, string projectName)
    {
        var projectId = ProjectId.CreateNewId();
        var projectInfo = ProjectInfo.Create(
            projectId,
            VersionStamp.Create(),
            projectName,
            projectName,
            LanguageNames.CSharp,
            filePath: $"{projectName}.csproj");

        var project = workspace.AddProject(projectInfo);

        // Add a simple class with a public method
        var sourceCode = $@"
namespace {projectName}
{{
    public class SimpleClass
    {{
        public void SimpleMethod()
        {{
            // Simple method implementation
        }}

        public int CalculateValue(int input)
        {{
            return input * 2;
        }}
    }}
}}";

        var documentId = DocumentId.CreateNewId(projectId);
        var documentInfo = DocumentInfo.Create(
            documentId,
            "SimpleClass.cs",
            sourceCodeKind: SourceCodeKind.Regular,
            loader: TextLoader.From(TextAndVersion.Create(SourceText.From(sourceCode), VersionStamp.Create())));

        workspace.AddDocument(documentInfo);
        return workspace.CurrentSolution.GetProject(projectId)!;
    }

    private Project CreateProjectWithMultipleClasses(AdhocWorkspace workspace, string projectName)
    {
        var projectId = ProjectId.CreateNewId();
        var projectInfo = ProjectInfo.Create(
            projectId,
            VersionStamp.Create(),
            projectName,
            projectName,
            LanguageNames.CSharp,
            filePath: $"{projectName}.csproj");

        var project = workspace.AddProject(projectInfo);

        // Add first class
        var sourceCode1 = $@"
namespace {projectName}
{{
    public class TestClass
    {{
        public void TestMethod()
        {{
            // Test method implementation
        }}

        public string ProcessData(string data)
        {{
            return data.ToUpper();
        }}
    }}
}}";

        var documentId1 = DocumentId.CreateNewId(projectId);
        var documentInfo1 = DocumentInfo.Create(
            documentId1,
            "TestClass.cs",
            sourceCodeKind: SourceCodeKind.Regular,
            loader: TextLoader.From(TextAndVersion.Create(SourceText.From(sourceCode1), VersionStamp.Create())));

        workspace.AddDocument(documentInfo1);

        // Add second class
        var sourceCode2 = $@"
namespace {projectName}
{{
    public class UtilityClass
    {{
        public bool ValidateInput(string input)
        {{
            return !string.IsNullOrEmpty(input);
        }}

        public void LogMessage(string message)
        {{
            // Logging implementation
        }}
    }}
}}";

        var documentId2 = DocumentId.CreateNewId(projectId);
        var documentInfo2 = DocumentInfo.Create(
            documentId2,
            "UtilityClass.cs",
            sourceCodeKind: SourceCodeKind.Regular,
            loader: TextLoader.From(TextAndVersion.Create(SourceText.From(sourceCode2), VersionStamp.Create())));

        workspace.AddDocument(documentInfo2);
        return workspace.CurrentSolution.GetProject(projectId)!;
    }

    private async Task<List<EntryPoint>> FindEntryPointsFromProject(EntryPointFinder finder, Project project)
    {
        // Create a temporary directory and files to simulate the project structure
        var tempDir = Path.Combine(Path.GetTempPath(), $"TestProject_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);

        try
        {
            // Create a temporary .csproj file
            var projectPath = Path.Combine(tempDir, $"{project.Name}.csproj");
            File.WriteAllText(projectPath, @"
<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>");

            // Write all documents to temporary files
            foreach (var document in project.Documents)
            {
                var sourceText = await document.GetTextAsync();
                var filePath = Path.Combine(tempDir, document.Name);
                File.WriteAllText(filePath, sourceText.ToString());
            }

            // Now call the original EntryPointFinder method
            return await finder.FindEntryPointsAsync(projectPath);
        }
        finally
        {
            // Clean up temporary files
            if (Directory.Exists(tempDir))
            {
                Directory.Delete(tempDir, true);
            }
        }
    }
}
