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
    
    [Test]
    public async Task MultiplePublicMethods_AllIdentifiedAsEntryPoints()
    {
        var projectPath = CreateProjectWithMultiplePublicMethods();

        var entryPoints = await EntryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(3));
        
        var methodNames = entryPoints.Select(ep => ep.FullyQualifiedName.Split('.').Last()).ToList();
        Assert.That(methodNames, Contains.Item("Add"));
        Assert.That(methodNames, Contains.Item("Subtract"));
        Assert.That(methodNames, Contains.Item("GetName"));
        
        var addMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("Add"));
        Assert.That(addMethod.MethodSignature, Is.EqualTo("int Add(int a, int b)"));
        
        var subtractMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("Subtract"));
        Assert.That(subtractMethod.MethodSignature, Is.EqualTo("int Subtract(int a, int b)"));
        
        var getNameMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("GetName"));
        Assert.That(getNameMethod.MethodSignature, Is.EqualTo("string GetName()"));
    }
    
    [Test]
    public async Task MultipleClasses_AllPublicMethodsIdentifiedAsEntryPoints()
    {
        var projectPath = CreateProjectWithMultipleClasses();

        var entryPoints = await EntryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(5));
        
        var calculatorMethods = entryPoints
            .Where(ep => ep.FullyQualifiedName.Contains("Calculator"))
            .ToList();
        Assert.That(calculatorMethods, Has.Count.EqualTo(2));
        
        var loggerMethods = entryPoints
            .Where(ep => ep.FullyQualifiedName.Contains("Logger"))
            .ToList();
        Assert.That(loggerMethods, Has.Count.EqualTo(1));
        
        var validatorMethods = entryPoints
            .Where(ep => ep.FullyQualifiedName.Contains("Validator"))
            .ToList();
        Assert.That(validatorMethods, Has.Count.EqualTo(2));
        
        var methodNames = entryPoints.Select(ep => ep.FullyQualifiedName.Split('.').Last()).ToList();
        Assert.That(methodNames, Contains.Item("Add"));
        Assert.That(methodNames, Contains.Item("Subtract"));
        Assert.That(methodNames, Contains.Item("Log"));
        Assert.That(methodNames, Contains.Item("IsValid"));
        Assert.That(methodNames, Contains.Item("GetErrorMessage"));
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
    
    private string CreateProjectWithMultiplePublicMethods()
    {
        var projectDir = Path.Combine(Path.GetTempPath(), "MultiMethodProject");
        Directory.CreateDirectory(projectDir);
        
        var projectPath = Path.Combine(projectDir, "MultiMethodProject.csproj");
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
        
        var sourceFilePath = Path.Combine(sourceDir, "Calculator.cs");
        File.WriteAllText(sourceFilePath, @"
namespace MultiMethodProject
{
    public class Calculator
    {
        public int Add(int a, int b)
        {
            return a + b;
        }
        
        public int Subtract(int a, int b)
        {
            return a - b;
        }
        
        public string GetName()
        {
            return ""Calculator"";
        }
        
        private int Multiply(int a, int b)
        {
            return a * b;
        }
    }
}"
        );
        
        return projectPath;
    }
    
    private string CreateProjectWithMultipleClasses()
    {
        var projectDir = Path.Combine(Path.GetTempPath(), "MultiClassProject");
        Directory.CreateDirectory(projectDir);
        
        var projectPath = Path.Combine(projectDir, "MultiClassProject.csproj");
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
        
        var calculatorFilePath = Path.Combine(sourceDir, "Calculator.cs");
        File.WriteAllText(calculatorFilePath, @"
namespace MultiClassProject
{
    public class Calculator
    {
        public int Add(int a, int b)
        {
            return a + b;
        }
        
        public int Subtract(int a, int b)
        {
            return a - b;
        }
        
        private int Multiply(int a, int b)
        {
            return a * b;
        }
    }
}"
        );
        
        var loggerFilePath = Path.Combine(sourceDir, "Logger.cs");
        File.WriteAllText(loggerFilePath, @"
namespace MultiClassProject
{
    public class Logger
    {
        public void Log(string message)
        {
            // Log the message
        }
        
        private void LogToFile(string message)
        {
            // Log to file
        }
    }
}"
        );
        
        var validatorFilePath = Path.Combine(sourceDir, "Validator.cs");
        File.WriteAllText(validatorFilePath, @"
namespace MultiClassProject
{
    public class Validator
    {
        public bool IsValid(string input)
        {
            return !string.IsNullOrEmpty(input);
        }
        
        public string GetErrorMessage()
        {
            return ""Invalid input"";
        }
    }
}"
        );
        
        return projectPath;
    }
}
