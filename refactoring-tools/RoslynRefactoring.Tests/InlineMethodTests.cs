using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class InlineMethodTests
{

    [Test]
    public async Task CanInlineSimple()
    {
        const string code = """
                            public class Calculator
                            {
                                public int Plus()
                                {
                                    return AddOneWithOne();
                                }

                                private int AddOneWithOne()
                                {
                                    return 1 + 1;
                                }
                            }
                            """;

        await VerifyInline(code, new Cursor(5,16));
    }

    private static async Task VerifyInline(string code, Cursor cursor)
    {
        var document = CreateDocument(code);
        var inlineMethod = new InlineMethod(cursor);
        var updatedDocument = await inlineMethod.PerformAsync(document);
        var formatted = Formatter.Format((await updatedDocument.GetSyntaxRootAsync())!, new AdhocWorkspace());
        await Verify(formatted.ToFullString());
    }

    private static Document CreateDocument(string code)
    {
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        return project.AddDocument("Test.cs", code);
    }
    [Test]
    public async Task CanInlineStaticMethodAcrossFiles()
    {
        const string mathHelperCode = """
                                      namespace MyProject.Utils
                                      {
                                          public static class MathHelper
                                          {
                                              public static double GetPi() => 3.14159;
                                          }
                                      }
                                      """;

        const string calculatorCode = """
                                      using MyProject.Utils;

                                      namespace MyProject.Services
                                      {
                                          public class Calculator
                                          {
                                              public double GetCircumference(double radius)
                                              {
                                                  return 2 * MathHelper.GetPi() * radius;
                                              }
                                          }
                                      }
                                      """;

        await VerifyInlineAcrossFiles(mathHelperCode, calculatorCode, new Cursor(8, 32)); // Position of GetPi() call
    }

    private static async Task VerifyInlineAcrossFiles(string sourceFileCode, string targetFileCode, Cursor cursor)
    {
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        // Add both files to the project
        project = project.AddDocument("Utils/MathHelper.cs", sourceFileCode).Project;
        var targetDocument = project.AddDocument("Services/Calculator.cs", targetFileCode);

        var inlineMethod = new InlineMethod(cursor);
        var updatedDocument = await inlineMethod.PerformAsync(targetDocument);
        var formatted = Formatter.Format((await updatedDocument.GetSyntaxRootAsync())!, new AdhocWorkspace());
        await Verify(formatted.ToFullString());
    }

    [Test]
    public async Task CanInlineStaticMethodWithOneParameterAcrossFiles()
    {
        const string mathHelperCode = """
                                      namespace MyProject.Utils
                                      {
                                          public static class MathHelper
                                          {
                                              public static int Square(int x) => x * x;
                                          }
                                      }
                                      """;

        const string calculatorCode = """
                                      using MyProject.Utils;

                                      namespace MyProject.Services
                                      {
                                          public class Calculator
                                          {
                                              public int CalculateArea(int side)
                                              {
                                                  return MathHelper.Square(side);
                                              }
                                          }
                                      }
                                      """;

        await VerifyInlineAcrossFiles(mathHelperCode, calculatorCode, new Cursor(8, 32)); // Position of Square() call
    }

    [Test]
    public async Task CanInlineStaticMethodWithTwoParametersAcrossFiles()
    {
        const string mathHelperCode = """
                                      namespace MyProject.Utils
                                      {
                                          public static class MathHelper
                                          {
                                              public static int Add(int a, int b) => a + b;
                                          }
                                      }
                                      """;

        const string calculatorCode = """
                                      using MyProject.Utils;

                                      namespace MyProject.Services
                                      {
                                          public class Calculator
                                          {
                                              public int CalculateSum(int x, int y)
                                              {
                                                  return MathHelper.Add(x, y);
                                              }
                                          }
                                      }
                                      """;

        await VerifyInlineAcrossFiles(mathHelperCode, calculatorCode, new Cursor(8, 32)); // Position of Add() call
    }

    [Test]
    public async Task CanInlineStaticMethodWithBlockBodyAcrossFiles()
    {
        const string mathHelperCode = """
                                      namespace MyProject.Utils
                                      {
                                          public static class MathHelper
                                          {
                                              public static int Max(int a, int b)
                                              {
                                                  return a > b ? a : b;
                                              }
                                          }
                                      }
                                      """;

        const string calculatorCode = """
                                      using MyProject.Utils;

                                      namespace MyProject.Services
                                      {
                                          public class Calculator
                                          {
                                              public int FindMaximum(int x, int y)
                                              {
                                                  return MathHelper.Max(x, y);
                                              }
                                          }
                                      }
                                      """;

        await VerifyInlineAcrossFiles(mathHelperCode, calculatorCode, new Cursor(8, 32)); // Position of Max() call
    }

    [Test]
    public async Task CanInlineStaticMethodCalledMultipleTimesAcrossFiles()
    {
        const string mathHelperCode = """
                                      namespace MyProject.Utils
                                      {
                                          public static class MathHelper
                                          {
                                              public static int Double(int x) => x * 2;
                                          }
                                      }
                                      """;

        const string calculatorCode = """
                                      using MyProject.Utils;

                                      namespace MyProject.Services
                                      {
                                          public class Calculator
                                          {
                                              public int ProcessNumbers(int a, int b)
                                              {
                                                  var first = MathHelper.Double(a);
                                                  var second = MathHelper.Double(b);
                                                  return first + second;
                                              }
                                          }
                                      }
                                      """;

        await VerifyInlineAcrossFiles(mathHelperCode, calculatorCode, new Cursor(9, 32)); // Position of first Double() call
    }
}
