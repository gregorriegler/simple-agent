using System.Text.Json;
using System.IO;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.MSBuild;
using Microsoft.Build.Locator;
using System.Collections.Immutable;

class Program
{
    static async Task Main(string[] args)
    {
        try
        {
            // Initialize MSBuildLocator
            MSBuildLocator.RegisterDefaults();
            
            if (args.Length == 0)
            {
                Console.WriteLine("Please provide the path to a .sln or .csproj file");
                return;
            }

            var solutionPath = Path.GetFullPath(args[0]);
            if (!File.Exists(solutionPath))
            {
                Console.Error.WriteLine($"File not found: {solutionPath}");
                return;
            }

            var entryPoints = await FindEntryPointsAsync(solutionPath);
            
            var options = new JsonSerializerOptions { WriteIndented = true };
            var json = JsonSerializer.Serialize(entryPoints, options);
            Console.WriteLine(json);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error: {ex.Message}");
            if (ex.InnerException != null)
            {
                Console.Error.WriteLine($"Inner exception: {ex.InnerException.Message}");
            }
            Environment.Exit(1);
        }
    }

    private static async Task<List<EntryPointInfo>> FindEntryPointsAsync(string solutionPath)
    {
        using var workspace = MSBuildWorkspace.Create();
        Solution solution;
        
        try
        {
            if (solutionPath.EndsWith(".sln", StringComparison.OrdinalIgnoreCase))
            {
                solution = await workspace.OpenSolutionAsync(solutionPath).ConfigureAwait(false);
            }
            else if (solutionPath.EndsWith(".csproj", StringComparison.OrdinalIgnoreCase))
            {
                var project = await workspace.OpenProjectAsync(solutionPath).ConfigureAwait(false);
                solution = project.Solution;
            }
            else
            {
                throw new ArgumentException("File must be a .sln or .csproj");
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error loading solution: {ex.Message}");
            return new List<EntryPointInfo>();
        }

        var entryPoints = new List<EntryPointInfo>();

        foreach (var project in solution.Projects)
        {
            var compilation = await project.GetCompilationAsync();
            if (compilation == null) continue;

            foreach (var tree in compilation.SyntaxTrees)
            {
                var semanticModel = compilation.GetSemanticModel(tree);
                var root = await tree.GetRootAsync();

                // Find all method declarations
                var methods = root.DescendantNodes().OfType<MethodDeclarationSyntax>();

                foreach (var method in methods)
                {
                    var methodSymbol = semanticModel.GetDeclaredSymbol(method);
                    if (methodSymbol == null) continue;

                    var containingType = methodSymbol.ContainingType;
                    if (containingType == null) continue;

                    // Skip non-public methods or methods in non-public types
                    if (methodSymbol.DeclaredAccessibility != Accessibility.Public ||
                        containingType.DeclaredAccessibility != Accessibility.Public)
                    {
                        continue;
                    }

                    // Determine confidence level
                    string confidence = "medium";
                    
                    // Check for high confidence indicators
                    if (IsControllerAction(methodSymbol) || 
                        IsMainMethod(method) ||
                        IsInterfaceImplementation(methodSymbol) ||
                        IsAsyncTaskHandler(method))
                    {
                        confidence = "high";
                    }

                    var entryPoint = new EntryPointInfo
                    {
                        Type = "EntryPoint",
                        Name = methodSymbol.Name,
                        DeclaringType = containingType.Name,
                        Namespace = containingType.ContainingNamespace?.ToString() ?? string.Empty,
                        File = tree.FilePath ?? string.Empty,
                        Signature = GetMethodSignature(methodSymbol),
                        LineNumber = method.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
                        Confidence = confidence
                    };

                    entryPoints.Add(entryPoint);
                }
            }
        }


        return entryPoints;
    }


    private static bool IsControllerAction(IMethodSymbol methodSymbol)
    {
        // Check if the containing type is a controller
        var baseType = methodSymbol.ContainingType.BaseType;
        while (baseType != null)
        {
            if (baseType.Name.Contains("Controller") || 
                baseType.ToDisplayString().Contains("ControllerBase"))
                return true;
            baseType = baseType.BaseType;
        }
        return false;
    }

    private static bool IsMainMethod(MethodDeclarationSyntax method)
    {
        // Check if this is the Main method
        return method.Identifier.Text == "Main" &&
               method.Modifiers.Any(m => m.IsKind(SyntaxKind.StaticKeyword));
    }

    private static bool IsInterfaceImplementation(IMethodSymbol methodSymbol)
    {
        // Check if the method implements an interface
        return methodSymbol.ExplicitInterfaceImplementations.Length > 0 ||
               methodSymbol.ContainingType.AllInterfaces
                   .SelectMany(@interface => @interface.GetMembers()
                       .OfType<IMethodSymbol>())
                   .Any(interfaceMethod => 
                       methodSymbol.ContainingType.FindImplementationForInterfaceMember(interfaceMethod)?.Equals(methodSymbol, SymbolEqualityComparer.Default) == true);
    }

    private static bool IsAsyncTaskHandler(MethodDeclarationSyntax method)
    {
        // Check for common async handler patterns
        string methodName = method.Identifier.Text;
        return methodName == "Handle" || 
               methodName == "HandleAsync" ||
               methodName == "Execute" || 
               methodName == "ExecuteAsync";
    }

    private static string GetMethodSignature(IMethodSymbol methodSymbol)
    {
        var returnType = methodSymbol.ReturnType.ToDisplayString(SymbolDisplayFormat.MinimallyQualifiedFormat);
        var parameters = string.Join(", ", methodSymbol.Parameters
            .Select(p => $"{p.Type} {p.Name}"));
            
        return $"{returnType} {methodSymbol.Name}({parameters})";
    }
}

class EntryPointInfo
{
    public string Type { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string DeclaringType { get; set; } = string.Empty;
    public string Namespace { get; set; } = string.Empty;
    public string File { get; set; } = string.Empty;
    public int LineNumber { get; set; }
    public string Signature { get; set; } = string.Empty;
    public string Confidence { get; set; } = "medium";
}
