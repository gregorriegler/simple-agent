using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace RoslynAnalysis;

public class MethodInfo
{
    public Document Document { get; }
    public MethodDeclarationSyntax MethodDeclaration { get; }
    public SemanticModel SemanticModel { get; }
    public string FullyQualifiedName { get; }

    public MethodInfo(Document document, MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel, string fullyQualifiedName)
    {
        Document = document;
        MethodDeclaration = methodDeclaration;
        SemanticModel = semanticModel;
        FullyQualifiedName = fullyQualifiedName;
    }
}

public class PublicMethodCollection
{
    public List<(EntryPoint entryPoint, Document document, MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel)> AllPublicMethods { get; }
    public List<MethodInfo> AllMethods { get; }

    public PublicMethodCollection(
        List<(EntryPoint entryPoint, Document document, MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel)> allPublicMethods,
        List<MethodInfo> allMethods)
    {
        AllPublicMethods = allPublicMethods;
        AllMethods = allMethods;
    }
}

public class EntryPointFinder
{
    private const int DEFAULT_REACHABLE_COUNT = 1;
    private static readonly string[] TEST_ATTRIBUTES = new[]
    {
        "Test",
        "TestMethod",
        "Fact",
        "Theory",
        "TestCase"
    };

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

        var documents = projects.SelectMany(p => p.Documents).ToList();

        var methodCollection = await CollectAllMethods(documents);

        var calledMethods = AnalyzeMethodCalls(methodCollection.AllPublicMethods);

        return FilterUncalledEntryPoints(methodCollection.AllPublicMethods, calledMethods, methodCollection.AllMethods);
    }


    private IMethodSymbol? CreateMethodSymbolResolver(MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel)
    {
        var methodSymbol = semanticModel.GetDeclaredSymbol(methodDeclaration);
        return methodSymbol;
    }

    private EntryPoint? TryCreateEntryPoint(
        Document document,
        MethodDeclarationSyntax methodDeclaration,
        SemanticModel semanticModel
    )
    {
        if (!methodDeclaration.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword)))
            return null;

        var methodSymbol = CreateMethodSymbolResolver(methodDeclaration, semanticModel);
        if (methodSymbol == null)
            return null;

        var containingType = methodSymbol.ContainingType;
        if (containingType == null)
            return null;

        if (IsTestMethod(methodSymbol))
            return null;

        var fullyQualifiedName = $"{containingType.ContainingNamespace.ToDisplayString()}.{containingType.Name}.{methodSymbol.Name}";

        var filePath = document.FilePath ?? string.Empty;

        var lineSpan = methodDeclaration.GetLocation().GetLineSpan();
        var lineNumber = lineSpan.StartLinePosition.Line + 1;

        var methodSignature = GetMethodSignature(methodSymbol);

        return new EntryPoint(
            fullyQualifiedName,
            filePath,
            lineNumber,
            methodSignature,
            DEFAULT_REACHABLE_COUNT
        );
    }

    private int CalculateReachableMethodsCount(
        MethodDeclarationSyntax methodDeclaration,
        SemanticModel semanticModel,
        List<MethodInfo> allMethods)
    {
        var reachableMethods = new HashSet<string>();
        var methodsToProcess = new Queue<(MethodDeclarationSyntax method, SemanticModel model)>();
        var processedMethods = new HashSet<string>();

        methodsToProcess.Enqueue((methodDeclaration, semanticModel));

        while (methodsToProcess.Count > 0)
        {
            var (currentMethod, currentSemanticModel) = methodsToProcess.Dequeue();
            var currentMethodSymbol = CreateMethodSymbolResolver(currentMethod, currentSemanticModel);
            if (currentMethodSymbol == null) continue;

            var currentMethodFullName = GetFullyQualifiedMethodName(currentMethodSymbol);

            if (processedMethods.Contains(currentMethodFullName))
                continue;

            processedMethods.Add(currentMethodFullName);
            reachableMethods.Add(currentMethodFullName);

            ProcessMethodInvocations(currentMethod, currentSemanticModel, allMethods, methodsToProcess, processedMethods);
        }

        return reachableMethods.Count;
    }

    private string GetMethodSignature(IMethodSymbol methodSymbol)
    {
        var returnType = GetSimplifiedTypeName(methodSymbol.ReturnType);
        var parameters = string.Join(", ", methodSymbol.Parameters.Select(p => $"{GetSimplifiedTypeName(p.Type)} {p.Name}"));
        return $"{returnType} {methodSymbol.Name}({parameters})";
    }

    private string GetSimplifiedTypeName(ITypeSymbol typeSymbol)
    {
        return typeSymbol.ToDisplayString(SymbolDisplayFormat.MinimallyQualifiedFormat);
    }

    private bool IsTestMethod(IMethodSymbol methodSymbol)
    {
        return methodSymbol.GetAttributes().Any(attr =>
            TEST_ATTRIBUTES.Any(testAttr =>
                attr.AttributeClass?.Name.Contains(testAttr) == true));
    }

    private string GetFullyQualifiedMethodName(IMethodSymbol methodSymbol)
    {
        return $"{methodSymbol.ContainingType.ContainingNamespace.ToDisplayString()}.{methodSymbol.ContainingType.Name}.{methodSymbol.Name}";
    }

    private async Task<PublicMethodCollection> CollectAllMethods(List<Document> documents)
    {
        var allPublicMethods = new List<(EntryPoint entryPoint, Document document, MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel)>();
        var allMethods = new List<MethodInfo>();

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
                var methodSymbol = CreateMethodSymbolResolver(methodDeclaration, semanticModel);
                if (methodSymbol != null)
                {
                    var fullyQualifiedName = GetFullyQualifiedMethodName(methodSymbol);
                    allMethods.Add(new MethodInfo(document, methodDeclaration, semanticModel, fullyQualifiedName));

                    var entryPoint = TryCreateEntryPoint(document, methodDeclaration, semanticModel);
                    if (entryPoint != null)
                    {
                        allPublicMethods.Add((entryPoint, document, methodDeclaration, semanticModel));
                    }
                }
            }
        }

        return new PublicMethodCollection(allPublicMethods, allMethods);
    }

    private HashSet<string> AnalyzeMethodCalls(List<(EntryPoint entryPoint, Document document, MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel)> allPublicMethods)
    {
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
                        var calledMethodFullName = GetFullyQualifiedMethodName(calledMethodSymbol);
                        calledMethods.Add(calledMethodFullName);
                    }
                }
            }
        }

        return calledMethods;
    }

    private List<EntryPoint> FilterUncalledEntryPoints(
        List<(EntryPoint entryPoint, Document document, MethodDeclarationSyntax methodDeclaration, SemanticModel semanticModel)> allPublicMethods,
        HashSet<string> calledMethods,
        List<MethodInfo> allMethods)
    {
        var entryPoints = new List<EntryPoint>();

        foreach (var (entryPoint, document, methodDeclaration, semanticModel) in allPublicMethods)
        {
            if (calledMethods.Contains(entryPoint.FullyQualifiedName))
                continue;

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

    private void ProcessMethodInvocations(
        MethodDeclarationSyntax currentMethod,
        SemanticModel currentSemanticModel,
        List<MethodInfo> allMethods,
        Queue<(MethodDeclarationSyntax method, SemanticModel model)> methodsToProcess,
        HashSet<string> processedMethods)
    {
        if (currentMethod.Body == null) return;

        var invocationExpressions = currentMethod.Body.DescendantNodes().OfType<InvocationExpressionSyntax>();

        foreach (var invocation in invocationExpressions)
        {
            var calledMethodFullName = ResolveMethodSymbol(invocation, currentSemanticModel, currentMethod);

            if (calledMethodFullName != null)
            {
                var calledMethodInfo = allMethods
                    .FirstOrDefault(m => m.FullyQualifiedName == calledMethodFullName);

                if (calledMethodInfo?.MethodDeclaration != null)
                {
                    if (!processedMethods.Contains(calledMethodFullName))
                    {
                        methodsToProcess.Enqueue((calledMethodInfo.MethodDeclaration, calledMethodInfo.SemanticModel));
                    }
                }
            }
        }
    }

    private string? ResolveMethodSymbol(InvocationExpressionSyntax invocation, SemanticModel semanticModel, MethodDeclarationSyntax currentMethod)
    {
        var symbolInfo = semanticModel.GetSymbolInfo(invocation);

        if (symbolInfo.Symbol is IMethodSymbol calledMethodSymbol)
        {
            return GetFullyQualifiedMethodName(calledMethodSymbol);
        }

        if (invocation.Expression is IdentifierNameSyntax identifierName)
        {
            var methodName = identifierName.Identifier.ValueText;
            var fallbackMethodSymbol = CreateMethodSymbolResolver(currentMethod, semanticModel);
            if (fallbackMethodSymbol != null)
            {
                var currentNamespace = fallbackMethodSymbol.ContainingType.ContainingNamespace.ToDisplayString();
                var currentTypeName = fallbackMethodSymbol.ContainingType.Name;
                return $"{currentNamespace}.{currentTypeName}.{methodName}";
            }
        }

        return null;
    }
}
