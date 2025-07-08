using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using RoslynRefactoring;

var mathHelperCode = """
namespace MyProject.Utils
{
    public static class MathHelper
    {
        public static int Add(int a, int b) => a + b;
    }
}
""";

var calculatorCode = """
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

// Create workspace and project
var workspace = new AdhocWorkspace();
var project = workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
    .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

// Add both files to the project
project = project.AddDocument("Utils/MathHelper.cs", mathHelperCode).Project;
var targetDocument = project.AddDocument("Services/Calculator.cs", calculatorCode);

// Get semantic model and syntax tree
var root = await targetDocument.GetSyntaxRootAsync();
var semanticModel = await targetDocument.GetSemanticModelAsync();

// Find the invocation
var invocation = root.DescendantNodes().OfType<InvocationExpressionSyntax>().First();
Console.WriteLine($"Found invocation: {invocation}");

// Try to resolve symbol
var symbolInfo = semanticModel.GetSymbolInfo(invocation);
Console.WriteLine($"Symbol resolved: {symbolInfo.Symbol != null}");
Console.WriteLine($"Symbol: {symbolInfo.Symbol}");

// Try our custom resolution
if (symbolInfo.Symbol == null)
{
    Console.WriteLine("Trying custom resolution...");
    // Extract method name and type name
    if (invocation.Expression is MemberAccessExpressionSyntax memberAccess)
    {
        var methodName = memberAccess.Name.Identifier.ValueText;
        var typeName = memberAccess.Expression.ToString();
        Console.WriteLine($"Method: {methodName}, Type: {typeName}");

        // Search in compilation
        var allTypes = GetAllTypesFromCompilation(semanticModel.Compilation.GlobalNamespace);
        var foundTypes = allTypes.Where(t => t.Name == typeName).ToList();
        Console.WriteLine($"Found {foundTypes.Count} types named '{typeName}'");

        foreach (var type in foundTypes)
        {
            Console.WriteLine($"Type: {type.ToDisplayString()}");
            var methods = type.GetMembers(methodName).OfType<IMethodSymbol>().ToList();
            Console.WriteLine($"Found {methods.Count} methods named '{methodName}'");
            foreach (var method in methods)
            {
                Console.WriteLine($"Method: {method.ToDisplayString()}");
            }
        }
    }
}

static IEnumerable<INamedTypeSymbol> GetAllTypesFromCompilation(INamespaceSymbol namespaceSymbol)
{
    foreach (var type in namespaceSymbol.GetTypeMembers())
    {
        yield return type;
    }

    foreach (var childNamespace in namespaceSymbol.GetNamespaceMembers())
    {
        foreach (var type in GetAllTypesFromCompilation(childNamespace))
        {
            yield return type;
        }
    }
}
