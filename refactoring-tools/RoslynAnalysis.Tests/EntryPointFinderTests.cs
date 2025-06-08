using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.MSBuild;
using System.IO;
using System.Text.Json;

namespace RoslynAnalysis.Tests;

[TestFixture]
public class EntryPointFinderTests
{
    private EntryPointFinder _entryPointFinder;
    
    [SetUp]
    public void Setup()
    {
        var workspaceLoader = new MSBuildWorkspaceLoader();
        _entryPointFinder = new EntryPointFinder(workspaceLoader);
    }
    
    [Test]
    public async Task SinglePublicMethod_IsIdentifiedAsEntryPoint()
    {
        var projectPath = CreateSingleClassProject();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

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

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

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

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

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
    
    private (string projectPath, string sourceDir) CreateProjectBase(string projectName)
    {
        var projectDir = Path.Combine(Path.GetTempPath(), projectName);
        Directory.CreateDirectory(projectDir);
        
        var projectPath = Path.Combine(projectDir, $"{projectName}.csproj");
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
        
        return (projectPath, sourceDir);
    }
    
    private string CreateSourceFile(string sourceDir, string fileName, string fileContent)
    {
        var sourceFilePath = Path.Combine(sourceDir, fileName);
        File.WriteAllText(sourceFilePath, fileContent);
        return sourceFilePath;
    }
    
    private string CreateSingleClassProject()
    {
        var (projectPath, sourceDir) = CreateProjectBase("SimpleProject");
        
        CreateSourceFile(sourceDir, "SimpleClass.cs", @"
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
        var (projectPath, sourceDir) = CreateProjectBase("MultiMethodProject");
        
        CreateSourceFile(sourceDir, "Calculator.cs", @"
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
        var (projectPath, sourceDir) = CreateProjectBase("MultiClassProject");
        
        CreateSourceFile(sourceDir, "Calculator.cs", @"
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
        
        CreateSourceFile(sourceDir, "Logger.cs", @"
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
        
        CreateSourceFile(sourceDir, "Validator.cs", @"
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
