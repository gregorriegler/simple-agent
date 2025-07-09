using Microsoft.Build.Locator;

namespace RoslynAnalysis.Tests;

[TestFixture]
public class EntryPointFinderTests
{
    private EntryPointFinder _entryPointFinder;

    [OneTimeSetUp]
    public void OneTimeSetup()
    {
        try
        {
            MSBuildLocator.RegisterDefaults();
        }
        catch (Exception)
        {

        }
    }

    [SetUp]
    public void Setup()
    {
        _entryPointFinder = new EntryPointFinder();
    }

    [Test]
    public async Task SinglePublicMethod_IsIdentifiedAsEntryPoint()
    {
        var projectPath = CreateSingleClassProject();
        var projectName = Path.GetFileNameWithoutExtension(projectPath);

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(1));
        var entryPoint = entryPoints[0];
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
        Assert.That(entryPoints[0].FullyQualifiedName, Does.EndWith("Add"));
        Assert.That(entryPoints[1].FullyQualifiedName, Does.EndWith("Subtract").Or.EndsWith("GetName"));
        Assert.That(entryPoints[2].FullyQualifiedName, Does.EndWith("Subtract").Or.EndsWith("GetName"));

        var addMethod = entryPoints[0];
        Assert.That(addMethod.MethodSignature, Is.EqualTo("int Add(int a, int b)"));
        Assert.That(addMethod.ReachableMethodsCount, Is.EqualTo(2));

        var subtractMethod = entryPoints[1].FullyQualifiedName.EndsWith("Subtract") ? entryPoints[1] : entryPoints[2];
        Assert.That(subtractMethod.MethodSignature, Is.EqualTo("int Subtract(int a, int b)"));
        Assert.That(subtractMethod.ReachableMethodsCount, Is.EqualTo(1));

        var getNameMethod = entryPoints[1].FullyQualifiedName.EndsWith("GetName") ? entryPoints[1] : entryPoints[2];
        Assert.That(getNameMethod.MethodSignature, Is.EqualTo("string GetName()"));
        Assert.That(getNameMethod.ReachableMethodsCount, Is.EqualTo(1));
    }

    [Test]
    public async Task EntryPoints_AreSortedByReachableMethodsCountDescending()
    {
        var projectPath = CreateProjectWithMultiplePublicMethods();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(3));
        Assert.That(entryPoints[0].FullyQualifiedName, Does.EndWith("Add"), "First method should be Add");
        Assert.That(entryPoints[0].ReachableMethodsCount, Is.EqualTo(2));
        Assert.That(entryPoints[1].ReachableMethodsCount, Is.EqualTo(1),
            $"Method {entryPoints[1].FullyQualifiedName} should have ReachableMethodsCount = 1");
        Assert.That(entryPoints[2].ReachableMethodsCount, Is.EqualTo(1),
            $"Method {entryPoints[2].FullyQualifiedName} should have ReachableMethodsCount = 1");
        Assert.That(entryPoints[1].FullyQualifiedName,
            Does.EndWith("GetName").Or.EndsWith("Subtract"),
            $"Unexpected method: {entryPoints[1].FullyQualifiedName}");
        Assert.That(entryPoints[2].FullyQualifiedName,
            Does.EndWith("GetName").Or.EndsWith("Subtract"),
            $"Unexpected method: {entryPoints[2].FullyQualifiedName}");
    }

    [Test]
    public async Task MultipleClasses_AllPublicMethodsIdentifiedAsEntryPoints()
    {
        var projectPath = CreateProjectWithMultipleClasses();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(5));

        bool hasAdd = false;
        bool hasSubtract = false;
        bool hasLog = false;
        bool hasIsValid = false;
        bool hasGetErrorMessage = false;

        foreach (var entryPoint in entryPoints)
        {
            if (entryPoint.FullyQualifiedName.Contains("Calculator.Add"))
            {
                hasAdd = true;
                Assert.That(entryPoint.MethodSignature, Is.EqualTo("int Add(int a, int b)"));
            }
            else if (entryPoint.FullyQualifiedName.Contains("Calculator.Subtract"))
            {
                hasSubtract = true;
                Assert.That(entryPoint.MethodSignature, Is.EqualTo("int Subtract(int a, int b)"));
            }
            else if (entryPoint.FullyQualifiedName.Contains("Logger.Log"))
            {
                hasLog = true;
                Assert.That(entryPoint.MethodSignature, Is.EqualTo("void Log(string message)"));
            }
            else if (entryPoint.FullyQualifiedName.Contains("Validator.IsValid"))
            {
                hasIsValid = true;
                Assert.That(entryPoint.MethodSignature, Is.EqualTo("bool IsValid(string input)"));
            }
            else if (entryPoint.FullyQualifiedName.Contains("Validator.GetErrorMessage"))
            {
                hasGetErrorMessage = true;
                Assert.That(entryPoint.MethodSignature, Is.EqualTo("string GetErrorMessage()"));
            }
        }

        // Verify all expected methods were found
        Assert.That(hasAdd, Is.True, "Could not find Calculator.Add method");
        Assert.That(hasSubtract, Is.True, "Could not find Calculator.Subtract method");
        Assert.That(hasLog, Is.True, "Could not find Logger.Log method");
        Assert.That(hasIsValid, Is.True, "Could not find Validator.IsValid method");
        Assert.That(hasGetErrorMessage, Is.True, "Could not find Validator.GetErrorMessage method");
    }

    [Test]
    public async Task PublicMethodCallingOtherMethods_CountsReachableMethods()
    {
        var projectPath = CreateProjectWithMethodCalls();

        var entryPoints = await _entryPointFinder.FindEntryPointsAsync(projectPath);

        Assert.That(entryPoints, Has.Count.EqualTo(1));

        var entryPoint = entryPoints[0];
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

        var entryPoint = entryPoints[0];
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

        // Find methods by their known signatures since we know the expected outcome
        EntryPoint? addMethod = null;
        EntryPoint? processMethod = null;
        EntryPoint? calculateMethod = null;

        for (int i = 0; i < entryPoints.Count; i++)
        {
            if (entryPoints[i].FullyQualifiedName.EndsWith("Add"))
                addMethod = entryPoints[i];
            else if (entryPoints[i].FullyQualifiedName.EndsWith("ProcessData"))
                processMethod = entryPoints[i];
            else if (entryPoints[i].FullyQualifiedName.EndsWith("Calculate"))
                calculateMethod = entryPoints[i];
        }

        Assert.That(addMethod, Is.Not.Null, "Could not find Add method");
        Assert.That(addMethod.MethodSignature, Is.EqualTo("int Add(int a, int b)"));

        Assert.That(processMethod, Is.Not.Null, "Could not find ProcessData method");
        Assert.That(processMethod.MethodSignature, Is.EqualTo("string ProcessData(string input, bool validate)"));

        Assert.That(calculateMethod, Is.Not.Null, "Could not find Calculate method");
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

        var entryPoint = entryPoints[0];
        Assert.That(entryPoint.FullyQualifiedName, Is.EqualTo("CrossCallProject.OrderService.ProcessOrder"));
        Assert.That(entryPoint.MethodSignature, Is.EqualTo("string ProcessOrder(string orderId)"));
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

        var entryPoint = entryPoints[0];
        Assert.That(entryPoint.FullyQualifiedName, Does.EndWith(".CircularService.StartProcess"));
        Assert.That(entryPoint.MethodSignature, Is.EqualTo("string StartProcess(string input)"));
        // Should count reachable methods despite circular references:
        // StartProcess -> ProcessA -> ProcessB (circular reference back to ProcessA is detected and handled)
        // Total unique methods: StartProcess, ProcessA, ProcessB = 3
        Assert.That(entryPoint.ReachableMethodsCount, Is.EqualTo(3));
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
        Assert.That(entryPoints[0].FullyQualifiedName, Does.EndWith("Calculator.Add"));
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
