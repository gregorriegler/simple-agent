using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace RoslynAnalysis;

public class EntryPointFinder
{
    private readonly IWorkspaceLoader _workspaceLoader;
    
    public EntryPointFinder(IWorkspaceLoader workspaceLoader)
    {
        _workspaceLoader = workspaceLoader;
    }
    
    public async Task<List<EntryPoint>> FindEntryPointsAsync(string projectPath)
    {
        var project = await _workspaceLoader.LoadProjectAsync(projectPath);
        
        if (project == null)
            return new List<EntryPoint>();
            
        var documents = project.Documents.ToList();
        
        var entryPoints = new List<EntryPoint>();
        
        foreach (var document in documents)
        {
            var documentEntryPoints = await FindEntryPointsInDocumentAsync(document);
            entryPoints.AddRange(documentEntryPoints);
        }
        
        return entryPoints;
    }
    
    private async Task<List<EntryPoint>> FindEntryPointsInDocumentAsync(Document document)
    {
        var entryPoints = new List<EntryPoint>();
        
        var syntaxTree = await document.GetSyntaxTreeAsync();
        if (syntaxTree == null)
            return entryPoints;
            
        var semanticModel = await document.GetSemanticModelAsync();
        if (semanticModel == null)
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
    
    private EntryPoint? TryCreateEntryPoint(
        Document document, 
        MethodDeclarationSyntax methodDeclaration, 
        SemanticModel semanticModel
    )
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
        
        // Since we've already checked that methodSymbol is not null, we can safely pass it
        var methodSignature = GetMethodSignature(methodSymbol);
        
        // Calculate reachable methods: itself + directly called methods in the same class
        var reachableMethods = new HashSet<string> { methodSymbol.Name };
        if (methodDeclaration.Body != null)
        {
            var invocationExpressions = methodDeclaration.Body.DescendantNodes().OfType<InvocationExpressionSyntax>();
            foreach (var invocation in invocationExpressions)
            {
                var symbolInfo = semanticModel.GetSymbolInfo(invocation);
                if (symbolInfo.Symbol is IMethodSymbol calledMethodSymbol)
                {
                    // Only count methods in the same class (not static, not external)
                    if (SymbolEqualityComparer.Default.Equals(calledMethodSymbol.ContainingType, containingType))
                    {
                        reachableMethods.Add(calledMethodSymbol.Name);
                    }
                }
            }
        }
        return new EntryPoint(
            fullyQualifiedName,
            filePath,
            lineNumber,
            methodSignature,
            reachableMethods.Count
        );
    }
    
    private string GetMethodSignature(IMethodSymbol methodSymbol)
    {
        // This method is only called with non-null methodSymbol (enforced by the non-null assertion in the caller)
        var returnType = methodSymbol.ReturnType.ToDisplayString();
        var parameters = string.Join(", ", methodSymbol.Parameters.Select(p => $"{p.Type.ToDisplayString()} {p.Name}"));
        return $"{returnType} {methodSymbol.Name}({parameters})";
    }
}
