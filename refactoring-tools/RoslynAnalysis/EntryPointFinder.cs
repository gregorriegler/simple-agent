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

public static class EntryPointFinder
{
    public static async Task<List<EntryPoint>> FindEntryPointsAsync(string projectPath)
    {
        if (string.IsNullOrWhiteSpace(projectPath))
            throw new ArgumentException("Project path cannot be null or empty", nameof(projectPath));
            
        if (!File.Exists(projectPath))
            throw new FileNotFoundException($"Project file not found: {projectPath}", projectPath);
            
        MSBuildLocator.RegisterDefaults();
        
        using var workspace = MSBuildWorkspace.Create();
        
        var project = await workspace.OpenProjectAsync(projectPath);
        
        if (project == null)
            throw new InvalidOperationException($"Failed to load project: {projectPath}");
            
        var documents = project.Documents.ToList();
        
        var entryPoints = new List<EntryPoint>();
        
        foreach (var document in documents)
        {
            var documentEntryPoints = await FindEntryPointsInDocumentAsync(document);
            entryPoints.AddRange(documentEntryPoints);
        }
        
        return entryPoints;
    }
    
    private static async Task<List<EntryPoint>> FindEntryPointsInDocumentAsync(Document document)
    {
        var entryPoints = new List<EntryPoint>();
        
        var syntaxTree = await document.GetSyntaxTreeAsync();
        var semanticModel = await document.GetSemanticModelAsync();
        
        if (syntaxTree == null || semanticModel == null)
            return entryPoints;
            
        var root = await syntaxTree.GetRootAsync();
        
        var methodDeclarations = root.DescendantNodes().OfType<MethodDeclarationSyntax>();
        
        foreach (var methodDeclaration in methodDeclarations)
        {
            var entryPoint = TryCreateEntryPoint(document, methodDeclaration, semanticModel);
            if (entryPoint != null)
                entryPoints.Add(entryPoint);
        }
        
        return entryPoints;
    }
    
    private static EntryPoint? TryCreateEntryPoint(
        Document document, 
        MethodDeclarationSyntax methodDeclaration, 
        SemanticModel semanticModel)
    {
        if (!methodDeclaration.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword)))
            return null;
        
        var methodSymbol = semanticModel.GetDeclaredSymbol(methodDeclaration);
        if (methodSymbol == null)
            return null;
        
        var containingType = methodSymbol.ContainingType;
        if (containingType == null)
            return null;
        
        var fullyQualifiedName = $"{containingType.ContainingNamespace.ToDisplayString()}.{containingType.Name}.{methodSymbol.Name}";
        
        var filePath = document.FilePath ?? string.Empty;
        
        var lineSpan = methodDeclaration.GetLocation().GetLineSpan();
        var lineNumber = lineSpan.StartLinePosition.Line + 1;
        
        var methodSignature = GetMethodSignature(methodSymbol);
        
        var reachableMethodsCount = 1;
        
        return new EntryPoint(
            fullyQualifiedName,
            filePath,
            lineNumber,
            methodSignature,
            reachableMethodsCount);
    }
    
    private static string GetMethodSignature(IMethodSymbol methodSymbol)
    {
        var returnType = methodSymbol.ReturnType.ToDisplayString();
        var parameters = string.Join(", ", methodSymbol.Parameters.Select(p => $"{p.Type.ToDisplayString()} {p.Name}"));
        return $"{returnType} {methodSymbol.Name}({parameters})";
    }
}
