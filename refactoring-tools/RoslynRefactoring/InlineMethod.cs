using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace RoslynRefactoring;

/// <summary>
/// Inline a method call by replacing it with the method's body
/// Triggers CI rebuild to check for transient test failures
/// </summary>
public class InlineMethod(Cursor cursor) : IRefactoring
{
    public static InlineMethod Create(string[] args)
    {
        var cursor = Cursor.Parse(args[0]);
        return new InlineMethod(cursor);
    }

    public async Task<Document> PerformAsync(Document document)
    {
        var validationResult = await ValidateInvocationContext(document);
        if (validationResult == null) return document;

        var (root, semanticModel, invocation, methodSymbol, methodDeclaration, methodBody) = validationResult.Value;

        var allInvocations = ProcessAllInvocations(root, semanticModel, methodSymbol, methodDeclaration, methodBody);

        return document.WithSyntaxRoot(allInvocations);
    }

    private async Task<(SyntaxNode root, SemanticModel semanticModel, InvocationExpressionSyntax invocation, IMethodSymbol methodSymbol, MethodDeclarationSyntax methodDeclaration, BlockSyntax methodBody)?> ValidateInvocationContext(Document document)
    {
        var (root, semanticModel) = await PrepareDocumentAsync(document);
        if (root == null || semanticModel == null) return null;

        var invocation = FindInvocationAtCursor(root, cursor);
        if (invocation == null) return null;

        var methodSymbol = ValidateAndGetMethodSymbol(semanticModel, invocation);
        if (methodSymbol == null) return null;

        var (methodDeclaration, methodBody, _) = await PrepareMethodForInlining(methodSymbol, invocation);
        if (methodDeclaration == null || methodBody == null) return null;

        return (root, semanticModel, invocation, methodSymbol, methodDeclaration, methodBody);
    }

    private SyntaxNode ProcessAllInvocations(SyntaxNode root, SemanticModel semanticModel, IMethodSymbol methodSymbol, MethodDeclarationSyntax methodDeclaration, BlockSyntax methodBody)
    {
        // Find all invocations of the same method in the document
        var allInvocations = FindAllInvocationsOfMethod(root, semanticModel, methodSymbol);

        // Process invocations in reverse order (bottom to top) to avoid invalidating node references
        var newRoot = root;
        foreach (var inv in allInvocations.OrderByDescending(i => i.SpanStart))
        {
            // Find the current invocation in the updated tree
            var currentInvocation = newRoot.FindNode(inv.Span) as InvocationExpressionSyntax;
            if (currentInvocation != null)
            {
                var parameterMap = CreateParameterMapping(methodDeclaration, currentInvocation);
                newRoot = PerformInlining(newRoot, currentInvocation, methodBody, parameterMap);
            }
        }

        return newRoot;
    }

    private static async Task<(SyntaxNode? root, SemanticModel? semanticModel)> PrepareDocumentAsync(Document document)
    {
        var root = await document.GetSyntaxRootAsync();
        if (root == null) return (null, null);

        var semanticModel = await document.GetSemanticModelAsync();
        if (semanticModel == null) return (null, null);

        return (root, semanticModel);
    }

    private static int GetPositionFromLineColumn(SyntaxNode root, Cursor cursor)
    {
        var text = root.GetText();
        var linePosition = new Microsoft.CodeAnalysis.Text.LinePosition(cursor.Line - 1, cursor.Column - 1);
        return text.Lines.GetPosition(linePosition);
    }

    private static InvocationExpressionSyntax? FindInvocationAtCursor(SyntaxNode root, Cursor cursor)
    {
        var position = GetPositionFromLineColumn(root, cursor);
        var node = root.FindNode(new Microsoft.CodeAnalysis.Text.TextSpan(position, 0));

        return node.AncestorsAndSelf().OfType<InvocationExpressionSyntax>().FirstOrDefault() ??
               node.DescendantNodesAndSelf().OfType<InvocationExpressionSyntax>().FirstOrDefault();
    }

    private static IMethodSymbol? ValidateAndGetMethodSymbol(SemanticModel semanticModel, InvocationExpressionSyntax invocation)
    {
        var symbolInfo = semanticModel.GetSymbolInfo(invocation);
        var methodSymbol = symbolInfo.Symbol as IMethodSymbol;

        // If we found the symbol directly, return it
        if (methodSymbol != null)
        {
            return methodSymbol;
        }

        // If symbol resolution failed, try to find it across the project
        return FindMethodSymbolAcrossProject(semanticModel, invocation);
    }

    private static IMethodSymbol? FindMethodSymbolAcrossProject(SemanticModel semanticModel, InvocationExpressionSyntax invocation)
    {
        // Extract method name and containing type from the invocation
        if (invocation.Expression is not MemberAccessExpressionSyntax memberAccess)
            return null;

        var methodName = memberAccess.Name.Identifier.ValueText;
        var typeName = ExtractTypeName(memberAccess.Expression);

        if (string.IsNullOrEmpty(typeName))
            return null;

        // Search in the current compilation for the type
        return SearchInCompilation(semanticModel.Compilation, typeName, methodName);
    }

    private static string? ExtractTypeName(ExpressionSyntax expression)
    {
        return expression switch
        {
            IdentifierNameSyntax identifier => identifier.Identifier.ValueText,
            MemberAccessExpressionSyntax memberAccess => ExtractTypeName(memberAccess.Name),
            _ => null
        };
    }

    private static IMethodSymbol? SearchInCompilation(Compilation compilation, string typeName, string methodName)
    {
        // Search for types with the given name across all namespaces in the compilation
        var allTypes = GetAllTypesFromCompilation(compilation.GlobalNamespace);

        return allTypes
            .Where(type => type.Name == typeName)
            .SelectMany(type => type.GetMembers(methodName))
            .OfType<IMethodSymbol>()
            .FirstOrDefault();
    }

    private static IEnumerable<INamedTypeSymbol> GetAllTypesFromCompilation(INamespaceSymbol namespaceSymbol)
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

    private static async Task<(MethodDeclarationSyntax? methodDeclaration, BlockSyntax? methodBody, Dictionary<string, ExpressionSyntax>? parameterMap)> PrepareMethodForInlining(IMethodSymbol methodSymbol, InvocationExpressionSyntax invocation)
    {
        var methodDeclaration = await FindMethodDeclarationAsync(methodSymbol);
        if (methodDeclaration == null) return (null, null, null);

        var methodBody = methodDeclaration.Body ??
                         (methodDeclaration.ExpressionBody != null
                             ? SyntaxFactory.Block(
                                 SyntaxFactory.ReturnStatement(methodDeclaration.ExpressionBody.Expression))
                             : null);

        if (methodBody == null) return (null, null, null);

        var parameterMap = CreateParameterMapping(methodDeclaration, invocation);

        return (methodDeclaration, methodBody, parameterMap);
    }

    private static SyntaxNode PerformInlining(
        SyntaxNode root,
        InvocationExpressionSyntax invocation,
        BlockSyntax methodBody,
        Dictionary<string, ExpressionSyntax> parameterMap)
    {
        var inlinedStatements = InlineMethodBody(methodBody, parameterMap);
        return ReplaceInvocationWithInlinedCode(root, invocation, inlinedStatements);
    }

    private static List<InvocationExpressionSyntax> FindAllInvocationsOfMethod(
        SyntaxNode root,
        SemanticModel semanticModel,
        IMethodSymbol targetMethodSymbol)
    {
        var invocations = new List<InvocationExpressionSyntax>();

        foreach (var invocation in root.DescendantNodes().OfType<InvocationExpressionSyntax>())
        {
            var symbolInfo = semanticModel.GetSymbolInfo(invocation);
            IMethodSymbol? methodSymbol = symbolInfo.Symbol as IMethodSymbol;

            // If direct resolution failed, try cross-project search
            if (methodSymbol == null)
            {
                methodSymbol = FindMethodSymbolAcrossProject(semanticModel, invocation);
            }

            if (methodSymbol != null &&
                SymbolEqualityComparer.Default.Equals(methodSymbol, targetMethodSymbol))
            {
                invocations.Add(invocation);
            }
        }

        return invocations;
    }

    private static async Task<MethodDeclarationSyntax?> FindMethodDeclarationAsync(IMethodSymbol methodSymbol)
    {
        foreach (var syntaxReference in methodSymbol.DeclaringSyntaxReferences)
        {
            var syntaxNode = await syntaxReference.GetSyntaxAsync();
            if (syntaxNode is MethodDeclarationSyntax methodDeclaration)
            {
                return methodDeclaration;
            }
        }

        return null;
    }

    private static Dictionary<string, ExpressionSyntax> CreateParameterMapping(
        MethodDeclarationSyntax methodDeclaration,
        InvocationExpressionSyntax invocation)
    {
        var parameterMap = new Dictionary<string, ExpressionSyntax>();

        var parameters = methodDeclaration.ParameterList.Parameters;
        var arguments = invocation.ArgumentList.Arguments;

        for (int i = 0; i < Math.Min(parameters.Count, arguments.Count); i++)
        {
            var paramName = parameters[i].Identifier.ValueText;
            var argExpression = arguments[i].Expression;
            parameterMap[paramName] = argExpression;
        }

        return parameterMap;
    }

    private static List<StatementSyntax> InlineMethodBody(
        BlockSyntax methodBody,
        Dictionary<string, ExpressionSyntax> parameterMap)
    {
        var inlinedStatements = new List<StatementSyntax>();

        foreach (var statement in methodBody.Statements)
        {
            var inlinedStatement = ReplaceParametersInStatement(statement, parameterMap);

            if (inlinedStatement is ReturnStatementSyntax returnStatement)
            {
                if (returnStatement.Expression != null)
                {
                    inlinedStatements.Add(inlinedStatement);
                }
            }
            else
            {
                inlinedStatements.Add(inlinedStatement);
            }
        }

        return inlinedStatements;
    }

    private static StatementSyntax ReplaceParametersInStatement(
        StatementSyntax statement,
        Dictionary<string, ExpressionSyntax> parameterMap)
    {
        var rewriter = new ParameterReplacementRewriter(parameterMap);
        return (StatementSyntax)rewriter.Visit(statement);
    }

    private static SyntaxNode ReplaceInvocationWithInlinedCode(
        SyntaxNode root,
        InvocationExpressionSyntax invocation,
        List<StatementSyntax> inlinedStatements)
    {
        // If we have exactly one return statement, replace the invocation with the return expression
        var singleReturnResult = HandleSingleReturnStatement(root, invocation, inlinedStatements);
        if (singleReturnResult != null)
        {
            return singleReturnResult;
        }

        // For multiple statements or non-return statements, replace the containing statement
        return HandleMultipleStatements(root, invocation, inlinedStatements);
    }

    private static SyntaxNode HandleMultipleStatements(
        SyntaxNode root,
        InvocationExpressionSyntax invocation,
        List<StatementSyntax> inlinedStatements)
    {
        var containingStatement = invocation.FirstAncestorOrSelf<StatementSyntax>();
        if (containingStatement == null) return root;

        var newStatements = inlinedStatements.Select(s => s.WithTriviaFrom(containingStatement));

        if (inlinedStatements.Count == 1)
        {
            return root.ReplaceNode(containingStatement, newStatements.First());
        }

        return ReplaceInBlock(root, containingStatement, newStatements);
    }

    private static SyntaxNode ReplaceInBlock(
        SyntaxNode root,
        StatementSyntax containingStatement,
        IEnumerable<StatementSyntax> newStatements)
    {
        var parent = containingStatement.Parent;
        if (parent is BlockSyntax block)
        {
            var index = block.Statements.IndexOf(containingStatement);
            var newBlock = block.WithStatements(
                SyntaxFactory.List(
                    block.Statements.Take(index)
                        .Concat(newStatements)
                        .Concat(block.Statements.Skip(index + 1))
                )
            );
            return root.ReplaceNode(block, newBlock);
        }

        return root;
    }

    private static SyntaxNode? HandleSingleReturnStatement(
        SyntaxNode root,
        InvocationExpressionSyntax invocation,
        List<StatementSyntax> inlinedStatements)
    {
        if (inlinedStatements.Count == 1 && inlinedStatements[0] is ReturnStatementSyntax returnStatement && returnStatement.Expression != null)
        {
            return root.ReplaceNode(invocation, returnStatement.Expression.WithTriviaFrom(invocation));
        }
        return null;
    }

    private class ParameterReplacementRewriter(Dictionary<string, ExpressionSyntax> parameterMap) : CSharpSyntaxRewriter
    {
        public override SyntaxNode? VisitIdentifierName(IdentifierNameSyntax node)
        {
            var identifier = node.Identifier.ValueText;
            return parameterMap.TryGetValue(identifier, out var replacement)
                ? replacement.WithTriviaFrom(node)
                : base.VisitIdentifierName(node);
        }
    }
}
