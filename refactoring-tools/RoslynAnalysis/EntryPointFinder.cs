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
        var projects = await _workspaceLoader.LoadProjectsAsync(projectPath);
        
        if (!projects.Any())
            return new List<EntryPoint>();
            
        // Combine documents from all projects
        var documents = projects.SelectMany(p => p.Documents).ToList();
        
        // First pass: find all public methods and collect all methods for reachability analysis
        var allPublicMethods = new List<(EntryPoint entryPoint, Document document, MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel)>();
        var allMethods = new List<(Document document, MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel, string fullyQualifiedName)>();
        
        foreach (var document in documents)
        {
            var syntaxTree = await document.GetSyntaxTreeAsync();
            if (syntaxTree == null) continue;
                
            var semanticModel = await document.GetSemanticModelAsync();
            if (semanticModel == null) continue;
            
            var root = await syntaxTree.GetRootAsync();
            var methodDeclarations = root.DescendantNodes().OfType<MethodDeclarationSyntax>();
            
            foreach (var methodDeclaration in methodDeclarations)
            {
                var methodSymbol = semanticModel.GetDeclaredSymbol(methodDeclaration);
                if (methodSymbol != null)
                {
                    var fullyQualifiedName = $"{methodSymbol.ContainingType.ContainingNamespace.ToDisplayString()}.{methodSymbol.ContainingType.Name}.{methodSymbol.Name}";
                    allMethods.Add((document, methodDeclaration, semanticModel, fullyQualifiedName));
                    
                    // Only add to public methods if it's public
                    var entryPoint = TryCreateEntryPoint(document, methodDeclaration, semanticModel);
                    if (entryPoint != null)
                    {
                        allPublicMethods.Add((entryPoint, document, methodDeclaration, semanticModel));
                    }
                }
            }
        }
        
        // Second pass: identify which methods are called by other methods
        var calledMethods = new HashSet<string>();
        
        foreach (var (_, document, methodDeclaration, semanticModel) in allPublicMethods)
        {
            if (methodDeclaration.Body != null)
            {
                var invocationExpressions = methodDeclaration.Body.DescendantNodes().OfType<InvocationExpressionSyntax>();
                foreach (var invocation in invocationExpressions)
                {
                    var symbolInfo = semanticModel.GetSymbolInfo(invocation);
                    if (symbolInfo.Symbol is IMethodSymbol calledMethodSymbol)
                    {
                        var calledMethodFullName = $"{calledMethodSymbol.ContainingType.ContainingNamespace.ToDisplayString()}.{calledMethodSymbol.ContainingType.Name}.{calledMethodSymbol.Name}";
                        calledMethods.Add(calledMethodFullName);
                    }
                }
            }
        }
        
        // Third pass: calculate reachable methods for entry points and filter out called methods
        var entryPoints = new List<EntryPoint>();
        
        foreach (var (entryPoint, document, methodDeclaration, semanticModel) in allPublicMethods)
        {
            // Skip methods that are called by other methods (they're not true entry points)
            if (calledMethods.Contains(entryPoint.FullyQualifiedName))
                continue;
                
            // Calculate reachable methods across all classes
            var reachableCount = CalculateReachableMethodsCount(methodDeclaration, semanticModel, allMethods);
            
            var updatedEntryPoint = new EntryPoint(
                entryPoint.FullyQualifiedName,
                entryPoint.FilePath,
                entryPoint.LineNumber,
                entryPoint.MethodSignature,
                reachableCount
            );
            
            entryPoints.Add(updatedEntryPoint);
        }
        
        return entryPoints.OrderByDescending(ep => ep.ReachableMethodsCount).ToList();
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
        
        // Exclude test methods - check for common test attributes
        if (IsTestMethod(methodSymbol))
            return null;
        
        var fullyQualifiedName = $"{containingType.ContainingNamespace.ToDisplayString()}.{containingType.Name}.{methodSymbol.Name}";
        
        var filePath = document.FilePath ?? string.Empty;
        
        var lineSpan = methodDeclaration.GetLocation().GetLineSpan();
        var lineNumber = lineSpan.StartLinePosition.Line + 1;
        
        // Since we've already checked that methodSymbol is not null, we can safely pass it
        var methodSignature = GetMethodSignature(methodSymbol);
        
        // Placeholder reachable count - will be recalculated later
        return new EntryPoint(
            fullyQualifiedName,
            filePath,
            lineNumber,
            methodSignature,
            1
        );
    }
    
    private int CalculateReachableMethodsCount(
        MethodDeclarationSyntax methodDeclaration,
        SemanticModel semanticModel,
        List<(Document document, MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel, string fullyQualifiedName)> allMethods)
    {
        var reachableMethods = new HashSet<string>();
        var methodsToProcess = new Queue<(MethodDeclarationSyntax method, SemanticModel model)>();
        var processedMethods = new HashSet<string>();
        
        methodsToProcess.Enqueue((methodDeclaration, semanticModel));
        
        while (methodsToProcess.Count > 0)
        {
            var (currentMethod, currentSemanticModel) = methodsToProcess.Dequeue();
            var currentMethodSymbol = currentSemanticModel.GetDeclaredSymbol(currentMethod);
            if (currentMethodSymbol == null) continue;
            
            var currentMethodFullName = $"{currentMethodSymbol.ContainingType.ContainingNamespace.ToDisplayString()}.{currentMethodSymbol.ContainingType.Name}.{currentMethodSymbol.Name}";
            
            // Check if we've already processed this method (prevents infinite loops in circular references)
            if (processedMethods.Contains(currentMethodFullName))
                continue;
                
            processedMethods.Add(currentMethodFullName);
            reachableMethods.Add(currentMethodFullName);
            
            if (currentMethod.Body != null)
            {
                var invocationExpressions = currentMethod.Body.DescendantNodes().OfType<InvocationExpressionSyntax>();
                
                foreach (var invocation in invocationExpressions)
                {
                    var symbolInfo = currentSemanticModel.GetSymbolInfo(invocation);
                    string? calledMethodFullName = null;
                    
                    if (symbolInfo.Symbol is IMethodSymbol calledMethodSymbol)
                    {
                        calledMethodFullName = $"{calledMethodSymbol.ContainingType.ContainingNamespace.ToDisplayString()}.{calledMethodSymbol.ContainingType.Name}.{calledMethodSymbol.Name}";
                    }
                    else
                    {
                        // Fallback: try to resolve by method name pattern matching
                        // This handles cases where symbol resolution fails due to circular references
                        if (invocation.Expression is IdentifierNameSyntax identifierName)
                        {
                            var methodName = identifierName.Identifier.ValueText;
                            var fallbackMethodSymbol = currentSemanticModel.GetDeclaredSymbol(currentMethod);
                            if (fallbackMethodSymbol != null)
                            {
                                var currentNamespace = fallbackMethodSymbol.ContainingType.ContainingNamespace.ToDisplayString();
                                var currentTypeName = fallbackMethodSymbol.ContainingType.Name;
                                calledMethodFullName = $"{currentNamespace}.{currentTypeName}.{methodName}";
                            }
                        }
                    }
                    
                    if (calledMethodFullName != null)
                    {
                        // Find the method declaration and its semantic model for the called method
                        var calledMethodInfo = allMethods
                            .FirstOrDefault(m => m.fullyQualifiedName == calledMethodFullName);
                            
                        if (calledMethodInfo.methodDeclaration != null)
                        {
                            // Only add to queue if we haven't processed this method yet
                            if (!processedMethods.Contains(calledMethodFullName))
                            {
                                methodsToProcess.Enqueue((calledMethodInfo.methodDeclaration, calledMethodInfo.semanticModel));
                            }
                        }
                    }
                }
            }
        }
        
        return reachableMethods.Count;
    }
    
    private string GetMethodSignature(IMethodSymbol methodSymbol)
    {
        // This method is only called with non-null methodSymbol (enforced by the non-null assertion in the caller)
        var returnType = GetSimplifiedTypeName(methodSymbol.ReturnType);
        var parameters = string.Join(", ", methodSymbol.Parameters.Select(p => $"{GetSimplifiedTypeName(p.Type)} {p.Name}"));
        return $"{returnType} {methodSymbol.Name}({parameters})";
    }
    
    private string GetSimplifiedTypeName(ITypeSymbol typeSymbol)
    {
        // Use Roslyn's built-in display format with C# keywords and minimal qualification
        return typeSymbol.ToDisplayString(SymbolDisplayFormat.MinimallyQualifiedFormat);
    }
    
    private bool IsTestMethod(IMethodSymbol methodSymbol)
    {
        // Check for common test attributes
        var testAttributes = new[]
        {
            "Test",
            "TestMethod", 
            "Fact",
            "Theory",
            "TestCase"
        };
        
        return methodSymbol.GetAttributes().Any(attr => 
            testAttributes.Any(testAttr => 
                attr.AttributeClass?.Name.Contains(testAttr) == true));
    }
}
