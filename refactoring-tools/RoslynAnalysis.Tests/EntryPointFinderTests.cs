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
        var projectName = Path.GetFileNameWithoutExtension(projectPath);

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(1));
        var entryPoint = entryPoints.First();
        Assert.That(entryPoint.FullyQualifiedName, Is.EqualTo($"{projectName}.SimpleClass.SimpleMethod"));
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
        Assert.That(addMethod.ReachableMethodsCount, Is.EqualTo(2));
        
        var subtractMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("Subtract"));
        Assert.That(subtractMethod.MethodSignature, Is.EqualTo("int Subtract(int a, int b)"));
        Assert.That(subtractMethod.ReachableMethodsCount, Is.EqualTo(1));
        
        var getNameMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("GetName"));
        Assert.That(getNameMethod.MethodSignature, Is.EqualTo("string GetName()"));
        Assert.That(getNameMethod.ReachableMethodsCount, Is.EqualTo(1));
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
    
    [Test]
    public async Task PublicMethodCallingOtherMethods_CountsReachableMethods()
    {
        var projectPath = CreateProjectWithMethodCalls();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(1));
        
        var entryPoint = entryPoints.First();
        Assert.That(entryPoint.FullyQualifiedName, Is.EqualTo("CallProject.BusinessLogic.ProcessData"));
        Assert.That(entryPoint.MethodSignature, Is.EqualTo("string ProcessData(string input)"));
        Assert.That(entryPoint.ReachableMethodsCount, Is.EqualTo(4)); // ProcessData + ValidateInput + TransformData + FormatOutput
    }
    
    [Test]
    public async Task MainMethod_IsRecognizedAsEntryPoint()
    {
        var projectPath = CreateProjectWithMainMethod();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(1));
        
        var entryPoint = entryPoints.First();
        Assert.That(entryPoint.FullyQualifiedName, Is.EqualTo("MainProject.Program.Main"));
        Assert.That(entryPoint.MethodSignature, Is.EqualTo("void Main(string[] args)"));
        Assert.That(entryPoint.ReachableMethodsCount, Is.EqualTo(1));
    }
    
    [Test]
    public async Task MethodWithParameters_IncludesParameterTypesInSignature()
    {
        var projectPath = CreateProjectWithParameterizedMethods();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(3));
        
        var addMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("Add"));
        Assert.That(addMethod.MethodSignature, Is.EqualTo("int Add(int a, int b)"));
        
        var processMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("ProcessData"));
        Assert.That(processMethod.MethodSignature, Is.EqualTo("string ProcessData(string input, bool validate)"));
        
        var calculateMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("Calculate"));
        Assert.That(calculateMethod.MethodSignature, Is.EqualTo("double Calculate(double x, double y, int precision)"));
    }
    
    [Test]
    public async Task MethodWithReturnValue_IncludesReturnTypeInSignature()
    {
        var projectPath = CreateProjectWithReturnValueMethods();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(4));
        
        var getNameMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("GetName"));
        Assert.That(getNameMethod.MethodSignature, Is.EqualTo("string GetName()"));
        
        var getCountMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("GetCount"));
        Assert.That(getCountMethod.MethodSignature, Is.EqualTo("int GetCount()"));
        
        var isValidMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("IsValid"));
        Assert.That(isValidMethod.MethodSignature, Is.EqualTo("bool IsValid()"));
        
        var getDataMethod = entryPoints.First(ep => ep.FullyQualifiedName.EndsWith("GetData"));
        Assert.That(getDataMethod.MethodSignature, Is.EqualTo("List<string> GetData()"));
    }
    
    [Test]
    public async Task CrossClassMethodCalls_CountsReachableMethodsAcrossClasses()
    {
        var projectPath = CreateProjectWithCrossClassCalls();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(1));
        
        var entryPoint = entryPoints.First();
        Assert.That(entryPoint.FullyQualifiedName, Is.EqualTo("CrossCallProject.OrderService.ProcessOrder"));
        Assert.That(entryPoint.MethodSignature, Is.EqualTo("string ProcessOrder(string orderId)"));
        // ProcessOrder calls: ValidateOrder (same class), PaymentService.ProcessPayment, EmailService.SendConfirmation
        // PaymentService.ProcessPayment calls: LogPayment (same class)
        // EmailService.SendConfirmation calls: FormatEmail (same class)
        // Total reachable: ProcessOrder + ValidateOrder + ProcessPayment + LogPayment + SendConfirmation + FormatEmail = 6
        Assert.That(entryPoint.ReachableMethodsCount, Is.EqualTo(6));
    }
    
    private string CreateProjectBase(string projectName)
    {
        var uniqueProjectName = $"{projectName}_{Guid.NewGuid():N}";
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
</Project>"
        );
        
        return projectPath;
    }
    
    private string CreateSourceFile(string projectDir, string fileName, string fileContent)
    {
        var sourceFilePath = Path.Combine(projectDir, fileName);
        File.WriteAllText(sourceFilePath, fileContent);
        return sourceFilePath;
    }
    
    private string CreateSingleClassProject()
    {
        var projectPath = CreateProjectBase("SimpleProject");
        var projectDir = Path.GetDirectoryName(projectPath)!;
        var projectName = Path.GetFileNameWithoutExtension(projectPath);
        
        CreateSourceFile(projectDir, "SimpleClass.cs", $@"
namespace {projectName}
{{
    public class SimpleClass
    {{
        public void SimpleMethod()
        {{
            
        }}
    }}
}}"
        );
        
        return projectPath;
    }
    
    private string CreateProjectWithMultiplePublicMethods()
    {
        var projectPath = CreateProjectBase("MultiMethodProject");
        var projectDir = Path.GetDirectoryName(projectPath)!;
        
        CreateSourceFile(projectDir, "Calculator.cs", @"
namespace MultiMethodProject
{
    public class Calculator
    {
        public int Add(int a, int b)
        {
            return Multiply(a, 1) + Multiply(b, 1);
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
        var projectPath = CreateProjectBase("MultiClassProject");
        var projectDir = Path.GetDirectoryName(projectPath)!;
        
        CreateSourceFile(projectDir, "Calculator.cs", @"
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
        
        CreateSourceFile(projectDir, "Logger.cs", @"
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
        
        CreateSourceFile(projectDir, "Validator.cs", @"
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
    
    private string CreateProjectWithMethodCalls()
    {
        var projectPath = CreateProjectBase("CallProject");
        var projectDir = Path.GetDirectoryName(projectPath)!;
        
        CreateSourceFile(projectDir, "BusinessLogic.cs", @"
namespace CallProject
{
    public class BusinessLogic
    {
        public string ProcessData(string input)
        {
            var validatedInput = ValidateInput(input);
            var transformedData = TransformData(validatedInput);
            return FormatOutput(transformedData);
        }
        
        private string ValidateInput(string input)
        {
            return string.IsNullOrEmpty(input) ? ""default"" : input;
        }
        
        private string TransformData(string data)
        {
            return data.ToUpper();
        }
        
        private string FormatOutput(string data)
        {
            return $""Result: {data}"";
        }
    }
}"
        );
        
        return projectPath;
    }
    
    private string CreateProjectWithMainMethod()
    {
        var projectPath = CreateProjectBase("MainProject");
        var projectDir = Path.GetDirectoryName(projectPath)!;
        
        CreateSourceFile(projectDir, "Program.cs", @"
namespace MainProject
{
    public class Program
    {
        public static void Main(string[] args)
        {
            Console.WriteLine(""Hello World!"");
        }
    }
}"
        );
        
        return projectPath;
    }
    
    private string CreateProjectWithParameterizedMethods()
    {
        var projectPath = CreateProjectBase("ParameterProject");
        var projectDir = Path.GetDirectoryName(projectPath)!;
        
        CreateSourceFile(projectDir, "MathOperations.cs", @"
namespace ParameterProject
{
    public class MathOperations
    {
        public int Add(int a, int b)
        {
            return a + b;
        }
        
        public string ProcessData(string input, bool validate)
        {
            if (validate && string.IsNullOrEmpty(input))
                return ""Invalid"";
            return input?.ToUpper() ?? ""Empty"";
        }
        
        public double Calculate(double x, double y, int precision)
        {
            var result = x * y;
            return Math.Round(result, precision);
        }
    }
}"
        );
        
        return projectPath;
    }
    
    private string CreateProjectWithReturnValueMethods()
    {
        var projectPath = CreateProjectBase("ReturnValueProject");
        var projectDir = Path.GetDirectoryName(projectPath)!;
        
        CreateSourceFile(projectDir, "DataService.cs", @"
using System.Collections.Generic;

namespace ReturnValueProject
{
    public class DataService
    {
        public string GetName()
        {
            return ""DataService"";
        }
        
        public int GetCount()
        {
            return 42;
        }
        
        public bool IsValid()
        {
            return true;
        }
        
        public List<string> GetData()
        {
            return new List<string> { ""item1"", ""item2"", ""item3"" };
        }
    }
}"
        );
        
        return projectPath;
    }
    
    [Test]
    public async Task CircularReferences_HandledGracefully()
    {
        var projectPath = CreateProjectWithCircularReferences();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(1));
        
        var entryPoint = entryPoints.First();
        Assert.That(entryPoint.FullyQualifiedName, Does.EndWith(".CircularService.StartProcess"));
        Assert.That(entryPoint.MethodSignature, Is.EqualTo("string StartProcess(string input)"));
        // Should count reachable methods despite circular references:
        // StartProcess -> ProcessA -> ProcessB (circular reference back to ProcessA is detected and handled)
        // Total unique methods: StartProcess, ProcessA = 2
        Assert.That(entryPoint.ReachableMethodsCount, Is.EqualTo(2));
    }
    
    private string CreateProjectWithCircularReferences()
    {
        var projectName = $"CircularProject_{Guid.NewGuid():N}";
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
        
        // Create only the one source file we want
        var sourceFilePath = Path.Combine(projectDir, "CircularService.cs");
        File.WriteAllText(sourceFilePath, $@"
namespace {projectName}
{{
    public class CircularService
    {{
        public string StartProcess(string input)
        {{
            return ProcessA(input);
        }}
        
        private string ProcessA(string data)
        {{
            // This creates a circular reference: ProcessA -> ProcessB -> ProcessA
            return ProcessB(data + ""_A"");
        }}
        
        private string ProcessB(string data)
        {{
            if (data.Length > 10)
                return data; // Break the cycle conditionally
            
            // This creates the circular reference back to ProcessA
            return ProcessA(data + ""_B"");
        }}
    }}
}}"
        );
        
        return projectPath;
    }
    
    private string CreateProjectWithCrossClassCalls()
    {
        var projectPath = CreateProjectBase("CrossCallProject");
        var projectDir = Path.GetDirectoryName(projectPath)!;
        
        CreateSourceFile(projectDir, "OrderService.cs", @"
namespace CrossCallProject
{
    public class OrderService
    {
        private PaymentService _paymentService = new PaymentService();
        private EmailService _emailService = new EmailService();
        
        public string ProcessOrder(string orderId)
        {
            var isValid = ValidateOrder(orderId);
            if (!isValid) return ""Invalid order"";
            
            var paymentResult = _paymentService.ProcessPayment(orderId);
            _emailService.SendConfirmation(orderId);
            
            return $""Order {orderId} processed successfully"";
        }
        
        private bool ValidateOrder(string orderId)
        {
            return !string.IsNullOrEmpty(orderId);
        }
    }
}"
        );
        
        CreateSourceFile(projectDir, "PaymentService.cs", @"
namespace CrossCallProject
{
    public class PaymentService
    {
        public string ProcessPayment(string orderId)
        {
            LogPayment(orderId);
            return $""Payment processed for {orderId}"";
        }
        
        private void LogPayment(string orderId)
        {
            // Log payment details
        }
    }
}"
        );
        
        CreateSourceFile(projectDir, "EmailService.cs", @"
namespace CrossCallProject
{
    public class EmailService
    {
        public void SendConfirmation(string orderId)
        {
            var emailContent = FormatEmail(orderId);
            // Send email
        }
        
        private string FormatEmail(string orderId)
        {
            return $""Your order {orderId} has been confirmed."";
        }
    }
}"
        );
        
        return projectPath;
    }
    
    [Test]
    public async Task SolutionFile_LoadsAllProjectsAndFindsEntryPoints()
    {
        var solutionPath = CreateSolutionWithMultipleProjects();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(solutionPath);

        Assert.That(entryPoints, Has.Count.EqualTo(3));
        
        // Should find entry points from both projects
        var project1Methods = entryPoints.Where(ep => ep.FullyQualifiedName.Contains("Project1")).ToList();
        Assert.That(project1Methods, Has.Count.EqualTo(1));
        Assert.That(project1Methods.First().FullyQualifiedName, Does.EndWith("Calculator.Add"));
        
        var project2Methods = entryPoints.Where(ep => ep.FullyQualifiedName.Contains("Project2")).ToList();
        Assert.That(project2Methods, Has.Count.EqualTo(2));
        Assert.That(project2Methods.Any(ep => ep.FullyQualifiedName.EndsWith("Logger.Log")), Is.True);
        Assert.That(project2Methods.Any(ep => ep.FullyQualifiedName.EndsWith("Validator.IsValid")), Is.True);
    }
    
    private string CreateSolutionWithMultipleProjects()
    {
        var solutionName = $"TestSolution_{Guid.NewGuid():N}";
        var solutionDir = Path.Combine(Path.GetTempPath(), solutionName);
        Directory.CreateDirectory(solutionDir);
        
        // Create solution file
        var solutionPath = Path.Combine(solutionDir, $"{solutionName}.sln");
        
        // Create Project1
        var project1Dir = Path.Combine(solutionDir, "Project1");
        Directory.CreateDirectory(project1Dir);
        var project1Path = Path.Combine(project1Dir, "Project1.csproj");
        File.WriteAllText(project1Path, @"
<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>");
        
        CreateSourceFile(project1Dir, "Calculator.cs", @"
namespace Project1
{
    public class Calculator
    {
        public int Add(int a, int b)
        {
            return a + b;
        }
    }
}");
        
        // Create Project2
        var project2Dir = Path.Combine(solutionDir, "Project2");
        Directory.CreateDirectory(project2Dir);
        var project2Path = Path.Combine(project2Dir, "Project2.csproj");
        File.WriteAllText(project2Path, @"
<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>");
        
        CreateSourceFile(project2Dir, "Logger.cs", @"
namespace Project2
{
    public class Logger
    {
        public void Log(string message)
        {
            // Log implementation
        }
    }
}");
        
        CreateSourceFile(project2Dir, "Validator.cs", @"
namespace Project2
{
    public class Validator
    {
        public bool IsValid(string input)
        {
            return !string.IsNullOrEmpty(input);
        }
    }
}");
        
        // Create solution file content
        var project1Guid = Guid.NewGuid().ToString().ToUpper();
        var project2Guid = Guid.NewGuid().ToString().ToUpper();
        var solutionGuid = Guid.NewGuid().ToString().ToUpper();
        
        var solutionContent = $@"
Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project(""{{9A19103F-16F7-4668-BE54-9A1E7A4F7556}}"") = ""Project1"", ""Project1\Project1.csproj"", ""{{{project1Guid}}}""
EndProject
Project(""{{9A19103F-16F7-4668-BE54-9A1E7A4F7556}}"") = ""Project2"", ""Project2\Project2.csproj"", ""{{{project2Guid}}}""
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{{{project1Guid}}}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{{{project1Guid}}}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{{{project1Guid}}}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{{{project1Guid}}}.Release|Any CPU.Build.0 = Release|Any CPU
		{{{project2Guid}}}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{{{project2Guid}}}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{{{project2Guid}}}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{{{project2Guid}}}.Release|Any CPU.Build.0 = Release|Any CPU
	EndGlobalSection
	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
	GlobalSection(ExtensibilityGlobals) = postSolution
		SolutionGuid = {{{solutionGuid}}}
	EndGlobalSection
EndGlobal";
        
        File.WriteAllText(solutionPath, solutionContent);
        
        return solutionPath;
    }
    
    [Test]
    public async Task TestMethod_ExcludedFromEntryPoints()
    {
        var projectPath = CreateProjectWithTestMethod();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        // Should only find the production method, not the test method
        Assert.That(entryPoints, Has.Count.EqualTo(1));
        Assert.That(entryPoints.First().FullyQualifiedName, Does.EndWith("Calculator.Add"));
    }
    
    private string CreateSolutionWithProductionAndTestProjects()
    {
        var solutionName = $"ProdTestSolution_{Guid.NewGuid():N}";
        var solutionDir = Path.Combine(Path.GetTempPath(), solutionName);
        Directory.CreateDirectory(solutionDir);
        
        // Create solution file
        var solutionPath = Path.Combine(solutionDir, $"{solutionName}.sln");
        
        // Create Production Project
        var productionDir = Path.Combine(solutionDir, "ProductionProject");
        Directory.CreateDirectory(productionDir);
        var productionPath = Path.Combine(productionDir, "ProductionProject.csproj");
        File.WriteAllText(productionPath, @"
<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>");
        
        CreateSourceFile(productionDir, "Calculator.cs", @"
namespace ProductionProject
{
    public class Calculator
    {
        public int Add(int a, int b)
        {
            return a + b;
        }
    }
}");
        
        CreateSourceFile(productionDir, "Logger.cs", @"
namespace ProductionProject
{
    public class Logger
    {
        public void Log(string message)
        {
            // Log implementation
        }
    }
}");
        
        // Create Test Project
        var testDir = Path.Combine(solutionDir, "TestProject");
        Directory.CreateDirectory(testDir);
        var testPath = Path.Combine(testDir, "TestProject.csproj");
        File.WriteAllText(testPath, @"
<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include=""NUnit"" Version=""3.13.3"" />
  </ItemGroup>
  <ItemGroup>
    <ProjectReference Include=""..\ProductionProject\ProductionProject.csproj"" />
  </ItemGroup>
</Project>");
        
        CreateSourceFile(testDir, "CalculatorTests.cs", @"
using NUnit.Framework;
using ProductionProject;

namespace TestProject
{
    [TestFixture]
    public class CalculatorTests
    {
        [Test]
        public void Add_ShouldReturnSum()
        {
            var calculator = new Calculator();
            var result = calculator.Add(2, 3);
            Assert.That(result, Is.EqualTo(5));
        }
        
        [Test]
        public void Add_WithNegativeNumbers_ShouldWork()
        {
            var calculator = new Calculator();
            var result = calculator.Add(-2, 3);
            Assert.That(result, Is.EqualTo(1));
        }
    }
}");
        
        // Create solution file content
        var productionGuid = Guid.NewGuid().ToString().ToUpper();
        var testGuid = Guid.NewGuid().ToString().ToUpper();
        var solutionGuid = Guid.NewGuid().ToString().ToUpper();
        
        var solutionContent = $@"
Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project(""{{9A19103F-16F7-4668-BE54-9A1E7A4F7556}}"") = ""ProductionProject"", ""ProductionProject\ProductionProject.csproj"", ""{{{productionGuid}}}""
EndProject
Project(""{{9A19103F-16F7-4668-BE54-9A1E7A4F7556}}"") = ""TestProject"", ""TestProject\TestProject.csproj"", ""{{{testGuid}}}""
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{{{productionGuid}}}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{{{productionGuid}}}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{{{productionGuid}}}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{{{productionGuid}}}.Release|Any CPU.Build.0 = Release|Any CPU
		{{{testGuid}}}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{{{testGuid}}}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{{{testGuid}}}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{{{testGuid}}}.Release|Any CPU.Build.0 = Release|Any CPU
	EndGlobalSection
	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
	GlobalSection(ExtensibilityGlobals) = postSolution
		SolutionGuid = {{{solutionGuid}}}
	EndGlobalSection
EndGlobal";
        
        File.WriteAllText(solutionPath, solutionContent);
        
        return solutionPath;
    }
    
    private string CreateProjectWithTestMethod()
    {
        var projectPath = CreateProjectBase("TestMethodProject");
        var projectDir = Path.GetDirectoryName(projectPath)!;
        
        // Add NUnit package reference to the project file
        var projectContent = @"
<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include=""NUnit"" Version=""3.13.3"" />
  </ItemGroup>
</Project>";
        File.WriteAllText(projectPath, projectContent);
        
        CreateSourceFile(projectDir, "Calculator.cs", @"
using NUnit.Framework;

namespace TestMethodProject
{
    public class Calculator
    {
        public int Add(int a, int b)
        {
            return a + b;
        }
        
        [Test]
        public void TestAdd()
        {
            var result = Add(2, 3);
            Assert.That(result, Is.EqualTo(5));
        }
    }
}");
        
        return projectPath;
    }
}
