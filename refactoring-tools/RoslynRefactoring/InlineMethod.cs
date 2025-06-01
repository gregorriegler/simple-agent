using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace RoslynRefactoring;

public class InlineMethod(Cursor cursor) : IRefactoring
{
    public static InlineMethod Create(string[] args)
    {
        var cursor = Cursor.Parse(args[0]);
        return new InlineMethod(cursor);
    }

    public async Task<Document> PerformAsync(Document document)
    {
        var root = await document.GetSyntaxRootAsync();
        if (root == null) return document;

        var semanticModel = await document.GetSemanticModelAsync();
        if (semanticModel == null) return document;

        var position = GetPositionFromLineColumn(root, cursor);
        var node = root.FindNode(new Microsoft.CodeAnalysis.Text.TextSpan(position, 0));

        var invocation = node.AncestorsAndSelf().OfType<InvocationExpressionSyntax>().FirstOrDefault();
        if (invocation == null) return document;

        var symbolInfo = semanticModel.GetSymbolInfo(invocation);
        var methodSymbol = symbolInfo.Symbol as IMethodSymbol;
        if (methodSymbol == null) return document;

        var methodDeclaration = await FindMethodDeclarationAsync(methodSymbol);
        if (methodDeclaration == null) return document;

        var methodBody = methodDeclaration.Body ??
                         (methodDeclaration.ExpressionBody != null
                             ? SyntaxFactory.Block(
                                 SyntaxFactory.ReturnStatement(methodDeclaration.ExpressionBody.Expression))
                             : null);

        if (methodBody == null) return document;

        var parameterMap = CreateParameterMapping(methodDeclaration, invocation);

        var inlinedStatements = InlineMethodBody(methodBody, parameterMap);

        var newRoot = ReplaceInvocationWithInlinedCode(root, invocation, inlinedStatements);

        return document.WithSyntaxRoot(newRoot);
    }

    private static int GetPositionFromLineColumn(SyntaxNode root, Cursor cursor)
    {
        var text = root.GetText();
        var linePosition = new Microsoft.CodeAnalysis.Text.LinePosition(cursor.Line - 1, cursor.Column - 1);
        return text.Lines.GetPosition(linePosition);
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
        var containingStatement = invocation.FirstAncestorOrSelf<StatementSyntax>();
        if (containingStatement == null) return root;

        var newStatements = inlinedStatements.Select(s => s.WithTriviaFrom(containingStatement));

        if (inlinedStatements.Count == 1)
        {
            return root.ReplaceNode(containingStatement, newStatements.First());
        }

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