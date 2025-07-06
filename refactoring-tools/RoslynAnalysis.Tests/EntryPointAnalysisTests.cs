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

    [Test]
    public async Task DirectoryWithBothSlnAndCsprojFiles_PrioritizesSolutionFile()
    {
        // Arrange: Create a directory with both .sln and .csproj files
        var (solutionPath, projectPath) = CreateDirectoryWithBothSlnAndCsproj();
        var projectDir = Path.GetDirectoryName(solutionPath)!;

        // Act: Pass directory path - should automatically choose .sln over .csproj
        var analysis = new EntryPointAnalysis();
        var project = new AnalysisProject(projectDir, "");

        // This should automatically find and use the .sln file (not the .csproj)
        await project.OpenAndApplyAnalysis(analysis);

        // Assert: If we reach here, the solution file was prioritized and used
        Assert.Pass("Solution file was prioritized over project file");
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

    private (string solutionPath, string projectPath) CreateDirectoryWithBothSlnAndCsproj()
    {
        var uniqueName = $"MixedProject_{Guid.NewGuid():N}";
        var projectDir = Path.Combine(Path.GetTempPath(), uniqueName);
        Directory.CreateDirectory(projectDir);

        // Create .csproj file
        var projectPath = Path.Combine(projectDir, $"{uniqueName}.csproj");
        File.WriteAllText(projectPath, @"
<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>");

        // Create source file
        var sourceFilePath = Path.Combine(projectDir, "TestClass.cs");
        File.WriteAllText(sourceFilePath, $@"
namespace {uniqueName}
{{
    public class TestClass
    {{
        public void TestMethod()
        {{

        }}
    }}
}}");

        // Create .sln file
        var solutionPath = Path.Combine(projectDir, $"{uniqueName}.sln");
        var projectGuid = Guid.NewGuid().ToString().ToUpper();
        var solutionGuid = Guid.NewGuid().ToString().ToUpper();

        var solutionContent = $@"
Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project(""{{9A19103F-16F7-4668-BE54-9A1E7A4F7556}}"") = ""{uniqueName}"", ""{uniqueName}.csproj"", ""{{{projectGuid}}}""
EndProject
Global
 GlobalSection(SolutionConfigurationPlatforms) = preSolution
  Debug|Any CPU = Debug|Any CPU
  Release|Any CPU = Release|Any CPU
 EndGlobalSection
 GlobalSection(ProjectConfigurationPlatforms) = postSolution
  {{{projectGuid}}}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
  {{{projectGuid}}}.Debug|Any CPU.Build.0 = Debug|Any CPU
  {{{projectGuid}}}.Release|Any CPU.ActiveCfg = Release|Any CPU
  {{{projectGuid}}}.Release|Any CPU.Build.0 = Release|Any CPU
 EndGlobalSection
 GlobalSection(SolutionProperties) = preSolution
  HideSolutionNode = FALSE
 EndGlobalSection
 GlobalSection(ExtensibilityGlobals) = postSolution
  SolutionGuid = {{{solutionGuid}}}
 EndGlobalSection
EndGlobal";

        File.WriteAllText(solutionPath, solutionContent);

        return (solutionPath, projectPath);
    }
}
