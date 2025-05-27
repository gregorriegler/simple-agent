using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Editing;
using Microsoft.CodeAnalysis.Text;

namespace ExtractMethodTool;

public class ExtractMethod(CodeSelection selection, string newMethodName) : IRefactoring
{
    public static ExtractMethod Create(string[] args)
    {
        var selection = CodeSelection.Parse(args[0]);
        var newMethodName = args[1];
        return new ExtractMethod(selection, newMethodName);
    }
    
    public async Task<Document> PerformAsync(Document document)
    {
        var span = await GetSpan(document, selection);

        var root = await document.GetSyntaxRootAsync();
        if (root == null)
            throw new InvalidOperationException("SyntaxRoot is null.");

        var spanText = root.GetText().ToString(span);
        Console.WriteLine("\n=== Raw Span Content ===\n" + spanText);

        var selectedNode = root.FindNode(span);

        var selectedStatements = new List<StatementSyntax>();

        if (selectedNode is BlockSyntax blockNode)
        {
            selectedStatements = blockNode.Statements
                .Where(stmt => span.OverlapsWith(stmt.Span))
                .ToList();
        }
        else if (selectedNode is StatementSyntax singleStatement && span.OverlapsWith(singleStatement.Span))
        {
            selectedStatements.Add(singleStatement);
        }
        else
        {
            selectedStatements = selectedNode.DescendantNodesAndSelf()
                .OfType<StatementSyntax>()
                .Where(stmt => span.OverlapsWith(stmt.Span))
                .ToList();
        }

        if (selectedStatements.Count == 0)
            throw new InvalidOperationException("No statements selected for extraction.");

        var block = selectedNode.AncestorsAndSelf().OfType<BlockSyntax>().FirstOrDefault();
        if (block == null)
            throw new InvalidOperationException("Selected statements are not inside a block.");

        var model = await document.GetSemanticModelAsync();
        var dataFlow = model.AnalyzeDataFlow(selectedStatements.First(), selectedStatements.Last());
        if (dataFlow == null)
            throw new InvalidOperationException("DataFlow is null.");

        var parameters = dataFlow.ReadInside.Except(dataFlow.WrittenInside)
            .OfType<ILocalSymbol>()
            .Select(s => SyntaxFactory.Parameter(SyntaxFactory.Identifier(s.Name))
                .WithType(SyntaxFactory.ParseTypeName(s.Type.ToDisplayString()))).ToList();

        var returns = dataFlow.DataFlowsOut.Intersect(dataFlow.WrittenInside, SymbolEqualityComparer.Default)
            .OfType<ILocalSymbol>()
            .ToList();

        var containsReturnStatements = selectedStatements
            .SelectMany(stmt => stmt.DescendantNodesAndSelf().OfType<ReturnStatementSyntax>())
            .Any();

        var allPathsReturnOrThrow = selectedStatements is [SwitchStatementSyntax switchStatement]
                                    && switchStatement.Sections.All(sec =>
                                        sec.Statements.LastOrDefault() is ReturnStatementSyntax
                                            or ThrowStatementSyntax);

        TypeSyntax returnType;
        
        if (containsReturnStatements || allPathsReturnOrThrow)
        {
            var containingMethod = block.Ancestors().OfType<MethodDeclarationSyntax>().FirstOrDefault();
            if (containingMethod?.ReturnType != null)
            {
                returnType = containingMethod.ReturnType;
            }
            else
            {
                returnType = SyntaxFactory.PredefinedType(SyntaxFactory.Token(SyntaxKind.VoidKeyword));
            }
        }
        else if (returns.Count == 0)
        {
            returnType = SyntaxFactory.PredefinedType(SyntaxFactory.Token(SyntaxKind.VoidKeyword));
        }
        else if (returns.FirstOrDefault() is { } localReturnSymbol)
        {
            returnType = SyntaxFactory.ParseTypeName(localReturnSymbol.Type.ToDisplayString());
        }
        else
        {
            throw new InvalidOperationException("Unsupported return symbol type.");
        }

        var newMethodBody = SyntaxFactory.Block(selectedStatements);

        var invocationExpressionSyntax = SyntaxFactory.InvocationExpression(
            SyntaxFactory.IdentifierName(newMethodName),
            SyntaxFactory.ArgumentList(SyntaxFactory.SeparatedList(parameters.Select(p =>
                SyntaxFactory.Argument(SyntaxFactory.IdentifierName(p.Identifier.Text))))));

        StatementSyntax callStatement;
        
        if (containsReturnStatements || allPathsReturnOrThrow)
        {
            callStatement = SyntaxFactory.ReturnStatement(invocationExpressionSyntax);
        }
        else if (returns.Count == 0)
        {
            callStatement = SyntaxFactory.ExpressionStatement(invocationExpressionSyntax);
        }
        else if (returns.FirstOrDefault() is { } localReturnSymbol)
        {
            StatementSyntax returnStatement = SyntaxFactory.ReturnStatement(SyntaxFactory.IdentifierName(localReturnSymbol.Name));

            if (selectedStatements.Count == 1 && selectedStatements.First() is ReturnStatementSyntax)
            {
                callStatement = SyntaxFactory.ReturnStatement(invocationExpressionSyntax);
            }
            else
            {
                callStatement = SyntaxFactory.LocalDeclarationStatement(
                    SyntaxFactory.VariableDeclaration(returnType)
                        .WithVariables(SyntaxFactory.SingletonSeparatedList(
                            SyntaxFactory.VariableDeclarator(SyntaxFactory.Identifier(localReturnSymbol.Name))
                                .WithInitializer(SyntaxFactory.EqualsValueClause(invocationExpressionSyntax)))));
            }

            newMethodBody = newMethodBody.AddStatements(returnStatement);
        }
        else
        {
            throw new InvalidOperationException("Unsupported return symbol type.");
        }

        var methodDeclaration = SyntaxFactory.MethodDeclaration(returnType, newMethodName)
            .AddModifiers(SyntaxFactory.Token(SyntaxKind.PrivateKeyword))
            .WithParameterList(SyntaxFactory.ParameterList(SyntaxFactory.SeparatedList(parameters)))
            .WithBody(newMethodBody);

        var editor = new SyntaxEditor(root, document.Project.Solution.Workspace.Services);
        editor.ReplaceNode(selectedStatements.First(), callStatement);
        foreach (var stmt in selectedStatements.Skip(1))
            editor.RemoveNode(stmt);

        var methodNode = block.Ancestors().OfType<MethodDeclarationSyntax>().FirstOrDefault();
        if (methodNode != null)
        {
            editor.InsertAfter(methodNode, methodDeclaration);
        }
        else
        {
            editor.InsertAfter(selectedStatements.Last(), methodDeclaration);
        }

        var newRoot = editor.GetChangedRoot().NormalizeWhitespace();
        
        Console.WriteLine($"✅ Extracted method '{newMethodName}'");
        return document.WithSyntaxRoot(newRoot);
    }

    private static async Task<TextSpan> GetSpan(Document document, CodeSelection selection)
    {
        var lines = (await document.GetTextAsync()).Lines;
        var span = TextSpan.FromBounds(
            GetPos(selection.Start),
            GetPos(selection.End)
        );
        return span;

        int GetPos(Cursor cursor) => lines[cursor.Line - 1].Start + cursor.Column - 1;
    }
}