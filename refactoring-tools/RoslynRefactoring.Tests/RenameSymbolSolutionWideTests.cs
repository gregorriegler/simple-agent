using Microsoft.CodeAnalysis;
using RoslynRefactoring.Tests.TestHelpers;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class RenameSymbolSolutionWideTests
{
    [Test]
    public void ShouldRenameMethodAcrossMultipleFiles()
    {
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

        var solution = DocumentTestHelper.CreateSolutionWithFiles(
            ("Calculator.cs", file1Code),
            ("MathService.cs", file2Code)
        );

        var calculatorDocument = solution.Projects.First().Documents.First(d => d.Name == "Calculator.cs");

        var renameSymbol = new RenameSymbol(Cursor.Parse("4:16"), "Sum"); // cursor on "Add" method name
        var updatedDocument = renameSymbol.PerformAsync(calculatorDocument).Result;

        var updatedSolution = updatedDocument.Project.Solution;

        var updatedCalculatorText = updatedDocument.GetTextAsync().Result.ToString();
        Assert.That(updatedCalculatorText, Does.Contain("public int Sum(int a, int b)"));
        Assert.That(updatedCalculatorText, Does.Not.Contain("public int Add(int a, int b)"));

        var mathServiceDocument = updatedSolution.Projects.First().Documents.First(d => d.Name == "MathService.cs");
        var updatedMathServiceText = mathServiceDocument.GetTextAsync().Result.ToString();
        Assert.That(updatedMathServiceText, Does.Contain("calc.Sum(5, 3)"));
        Assert.That(updatedMathServiceText, Does.Not.Contain("calc.Add(5, 3)"));
    }

}
