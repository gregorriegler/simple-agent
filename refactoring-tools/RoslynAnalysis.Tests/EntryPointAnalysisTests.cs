using Microsoft.CodeAnalysis;

namespace RoslynAnalysis.Tests;

[TestFixture]
public class EntryPointAnalysisTests
{
    [Test]
    public async Task DirectoryWithSingleCsprojFile_AutomaticallyDetectsAndUsesProjectFile()
    {
        // Arrange: Create a directory with a single .csproj file
        var projectPath = CreateSingleClassProject();
        var projectDir = Path.GetDirectoryName(projectPath)!;

        // Act: Pass directory path instead of explicit .csproj file path
        var analysis = new EntryPointAnalysis();
        var project = new AnalysisProject(projectDir, "");

        // This should automatically find and use the .csproj file in the directory
        // Currently this will fail because AnalysisProject expects a file path, not directory
        await project.OpenAndApplyAnalysis(analysis);

        // Assert: If we reach here, the directory was successfully processed
        Assert.Pass("Directory analysis completed successfully");
    }

    private string CreateSingleClassProject()
    {
        var uniqueProjectName = $"AutoDetectProject_{Guid.NewGuid():N}";
        var projectDir = Path.Combine(Path.GetTempPath(), uniqueProjectName);
        Directory.CreateDirectory(projectDir);

        var projectPath = Path.Combine(projectDir, $"{uniqueProjectName}.csproj");
        File.WriteAllText(projectPath, @"
<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>");

        var sourceFilePath = Path.Combine(projectDir, "SimpleClass.cs");
        File.WriteAllText(sourceFilePath, $@"
namespace {uniqueProjectName}
{{
    public class SimpleClass
    {{
        public void SimpleMethod()
        {{

        }}
    }}
}}");

        return projectPath;
    }
}
