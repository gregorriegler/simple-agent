using Microsoft.CodeAnalysis;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class RenameSymbolSolutionWideTests
{
    [Test]
    public void ShouldRenameMethodAcrossMultipleFiles()
    {
        // Arrange: Create a solution with two files
        var file1Code = @"
public class Calculator
{
    public int Add(int a, int b)
    {
        return a + b;
    }
}";

        var file2Code = @"
public class MathService
{
    private Calculator calc = new Calculator();
    
    public int DoMath()
    {
        return calc.Add(5, 3);
    }
}";

        var solution = CreateSolutionWithFiles(
            ("Calculator.cs", file1Code),
            ("MathService.cs", file2Code)
        );
        
        var calculatorDocument = solution.Projects.First().Documents.First(d => d.Name == "Calculator.cs");
        
        // Act: Rename the Add method in Calculator.cs
        var renameSymbol = new RenameSymbol(Cursor.Parse("4:16"), "Sum"); // cursor on "Add" method name
        var updatedDocument = renameSymbol.PerformAsync(calculatorDocument).Result;
        
        // Assert: Both files should be updated
        var updatedSolution = updatedDocument.Project.Solution;
        
        // Check Calculator.cs - method declaration should be renamed
        var updatedCalculatorText = updatedDocument.GetTextAsync().Result.ToString();
        Assert.That(updatedCalculatorText, Does.Contain("public int Sum(int a, int b)"));
        Assert.That(updatedCalculatorText, Does.Not.Contain("public int Add(int a, int b)"));
        
        // Check MathService.cs - method call should be renamed
        var mathServiceDocument = updatedSolution.Projects.First().Documents.First(d => d.Name == "MathService.cs");
        var updatedMathServiceText = mathServiceDocument.GetTextAsync().Result.ToString();
        Assert.That(updatedMathServiceText, Does.Contain("calc.Sum(5, 3)"));
        Assert.That(updatedMathServiceText, Does.Not.Contain("calc.Add(5, 3)"));
    }

    private static Solution CreateSolutionWithFiles(params (string fileName, string code)[] files)
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