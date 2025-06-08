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
    
    private async Task<List<EntryPoint>> FindEntryPointsInDocumentAsync(Document document)
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
    
    private EntryPoint? TryCreateEntryPoint(
        Document document, 
        MethodDeclarationSyntax methodDeclaration, 
        SemanticModel semanticModel
    )
    {
        if (!methodDeclaration.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword)))
            return null;
        
        var methodSymbol = semanticModel.GetDeclaredSymbol(methodDeclaration);
        var containingType = methodSymbol?.ContainingType;
        if (containingType == null)
            return null;
        
        var fullyQualifiedName = $"{containingType.ContainingNamespace.ToDisplayString()}.{containingType.Name}.{methodSymbol?.Name}";
        
        var filePath = document.FilePath ?? string.Empty;
        
        var lineSpan = methodDeclaration.GetLocation().GetLineSpan();
        var lineNumber = lineSpan.StartLinePosition.Line + 1;
        
        // Since we've already checked that containingType is not null, methodSymbol must also not be null
        // But we'll use the non-null assertion operator to make this explicit
        var methodSignature = GetMethodSignature(methodSymbol!);
        
        // Removed the unnecessary variable and directly use the value 1
        return new EntryPoint(
            fullyQualifiedName,
            filePath,
            lineNumber,
            methodSignature,
            1 // Hardcoded value as it's not actually calculated
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
