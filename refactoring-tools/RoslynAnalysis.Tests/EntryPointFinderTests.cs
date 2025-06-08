using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.MSBuild;
using System.IO;
using System.Text.Json;

namespace RoslynAnalysis.Tests;

[TestFixture]
public class EntryPointFinderTests
{
    [Test]
    public async Task SinglePublicMethod_IsIdentifiedAsEntryPoint()
    {
        var projectPath = CreateSingleClassProject();

        var entryPoints = await EntryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(1));
        var entryPoint = entryPoints.First();
        Assert.That(entryPoint.FullyQualifiedName, Is.EqualTo("SimpleProject.SimpleClass.SimpleMethod"));
        Assert.That(entryPoint.MethodSignature, Is.EqualTo("void SimpleMethod()"));
        Assert.That(entryPoint.ReachableMethodsCount, Is.EqualTo(1));
    }
    
    private string CreateSingleClassProject()
    {
        var projectDir = Path.Combine(Path.GetTempPath(), "SimpleProject");
        Directory.CreateDirectory(projectDir);
        
        var projectPath = Path.Combine(projectDir, "SimpleProject.csproj");
        File.WriteAllText(projectPath, @"
<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>"
);
        
        var sourceDir = Path.Combine(projectDir, "src");
        Directory.CreateDirectory(sourceDir);
        
        var sourceFilePath = Path.Combine(sourceDir, "SimpleClass.cs");
        File.WriteAllText(sourceFilePath, @"
namespace SimpleProject
{
    public class SimpleClass
    {
        public void SimpleMethod()
        {
            
        }
    }
}"
);
        
        return projectPath;
    }
}
