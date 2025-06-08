using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.MSBuild;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace RoslynAnalysis;

/// <summary>
/// Analyzes a C# codebase to find entry points for characterization testing.
/// </summary>
public static class EntryPointFinder
{
    /// <summary>
    /// Finds entry points in a C# project.
    /// </summary>
    /// <param name="projectPath">Path to the C# project file.</param>
    /// <returns>A list of entry points with metadata.</returns>
    public static async Task<List<EntryPoint>> FindEntryPointsAsync(string projectPath)
    {
        // Validate input
        if (string.IsNullOrWhiteSpace(projectPath))
            throw new ArgumentException("Project path cannot be null or empty", nameof(projectPath));
            
        if (!File.Exists(projectPath))
            throw new FileNotFoundException($"Project file not found: {projectPath}", projectPath);
            
        // Register MSBuild instance
        MSBuildLocator.RegisterDefaults();
        
        // Create MSBuild workspace
        using var workspace = MSBuildWorkspace.Create();
        
        // Open the project
        var project = await workspace.OpenProjectAsync(projectPath);
        
        if (project == null)
            throw new InvalidOperationException($"Failed to load project: {projectPath}");
            
        // Get all documents in the project
        var documents = project.Documents.ToList();
        
        var entryPoints = new List<EntryPoint>();
        
        // Process each document
        foreach (var document in documents)
        {
            var documentEntryPoints = await FindEntryPointsInDocumentAsync(document);
            entryPoints.AddRange(documentEntryPoints);
        }
        
        return entryPoints;
    }
    
    /// <summary>
    /// Finds entry points in a single document.
    /// </summary>
    private static async Task<List<EntryPoint>> FindEntryPointsInDocumentAsync(Document document)
    {
        var entryPoints = new List<EntryPoint>();
        
        var syntaxTree = await document.GetSyntaxTreeAsync();
        var semanticModel = await document.GetSemanticModelAsync();
        
        if (syntaxTree == null || semanticModel == null)
            return entryPoints;
            
        var root = await syntaxTree.GetRootAsync();
        
        // Find all method declarations
        var methodDeclarations = root.DescendantNodes().OfType<MethodDeclarationSyntax>();
        
        foreach (var methodDeclaration in methodDeclarations)
        {
            var entryPoint = TryCreateEntryPoint(document, methodDeclaration, semanticModel);
            if (entryPoint != null)
                entryPoints.Add(entryPoint);
        }
        
        return entryPoints;
    }
    
    /// <summary>
    /// Tries to create an entry point from a method declaration.
    /// </summary>
    private static EntryPoint? TryCreateEntryPoint(
        Document document, 
        MethodDeclarationSyntax methodDeclaration, 
        SemanticModel semanticModel)
    {
        // Check if the method is public
        if (!methodDeclaration.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword)))
            return null;
        
        // Get method symbol
        var methodSymbol = semanticModel.GetDeclaredSymbol(methodDeclaration);
        if (methodSymbol == null)
            return null;
        
        // Get containing type
        var containingType = methodSymbol.ContainingType;
        if (containingType == null)
            return null;
        
        // Get fully qualified name
        var fullyQualifiedName = $"{containingType.ContainingNamespace.ToDisplayString()}.{containingType.Name}.{methodSymbol.Name}";
        
        // Get file path
        var filePath = document.FilePath ?? string.Empty;
        
        // Get line number
        var lineSpan = methodDeclaration.GetLocation().GetLineSpan();
        var lineNumber = lineSpan.StartLinePosition.Line + 1; // 1-based line number
        
        // Get method signature
        var methodSignature = GetMethodSignature(methodSymbol);
        
        // For now, just count this method itself as reachable
        var reachableMethodsCount = 1;
        
        return new EntryPoint(
            fullyQualifiedName,
            filePath,
            lineNumber,
            methodSignature,
            reachableMethodsCount);
    }
    
    /// <summary>
    /// Gets the method signature as a string.
    /// </summary>
    private static string GetMethodSignature(IMethodSymbol methodSymbol)
    {
        var returnType = methodSymbol.ReturnType.ToDisplayString();
        var parameters = string.Join(", ", methodSymbol.Parameters.Select(p => $"{p.Type.ToDisplayString()} {p.Name}"));
        return $"{returnType} {methodSymbol.Name}({parameters})";
    }
}
