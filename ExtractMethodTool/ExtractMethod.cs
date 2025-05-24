using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Editing;
using Microsoft.CodeAnalysis.Text;

namespace ExtractMethodTool;

public static class ExtractMethod
{
    public static async Task<SyntaxNode> RewriteAsync(Document document, string newMethodName,
        CodeSelection planSelection)
    {
        
        var text = await document.GetTextAsync();
        var lines = text.Lines;
        int GetPos(int line, int col) => lines[line - 1].Start + col - 1;

        var span = TextSpan.FromBounds(
            GetPos(planSelection.StartLine, planSelection.StartColumn),
            GetPos(planSelection.EndLine, planSelection.EndColumn)
        );
        
        var root = await document.GetSyntaxRootAsync();
        var model = await document.GetSemanticModelAsync();

        // Print raw span content
        var spanText = root.GetText().ToString(span);
        Console.WriteLine("\n=== Raw Span Content ===\n" + spanText);
        
        // Try to extract selected statements more robustly
        var selectedNode = root.FindNode(span);

        var selectedStatements = selectedNode is BlockSyntax blockNode
            ? blockNode.Statements.Where(stmt => span.OverlapsWith(stmt.Span)).ToList()
            : selectedNode.DescendantNodesAndSelf().OfType<StatementSyntax>()
                .Where(stmt => span.Contains(stmt.Span)).ToList();

        if (!selectedStatements.Any())
            throw new InvalidOperationException("No statements selected for extraction.");

        // Find the common block ancestor for editing context
        var block = selectedNode.AncestorsAndSelf().OfType<BlockSyntax>().FirstOrDefault();
        if (block == null)
            throw new InvalidOperationException("Selected statements are not inside a block.");

        var editor = new SyntaxEditor(root, document.Project.Solution.Workspace);

        // Data flow analysis to determine parameters and return values
        var dataFlow = model.AnalyzeDataFlow(selectedStatements.First(), selectedStatements.Last());

        var parameters = dataFlow.ReadInside.Except(dataFlow.WrittenInside)
            .OfType<ILocalSymbol>()
            .Select(s => SyntaxFactory.Parameter(SyntaxFactory.Identifier(s.Name))
                .WithType(SyntaxFactory.ParseTypeName(s.Type.ToDisplayString()))).ToList();

        var returns = dataFlow.DataFlowsOut.Intersect(dataFlow.WrittenInside)
            .OfType<ILocalSymbol>()
            .ToList();

        // Decide return type
        TypeSyntax returnType;
        StatementSyntax returnStatement = null;
        StatementSyntax callStatement;

        bool allPathsReturnOrThrow = selectedStatements.Count == 1 &&
            selectedStatements[0] is SwitchStatementSyntax switchStmt &&
            switchStmt.Sections.All(sec =>
                sec.Statements.LastOrDefault() is ReturnStatementSyntax or ThrowStatementSyntax);

        var returnSymbol = returns.FirstOrDefault();

        if (returns.Count == 0 && !allPathsReturnOrThrow)
        {
            returnType = SyntaxFactory.PredefinedType(SyntaxFactory.Token(SyntaxKind.VoidKeyword));
            callStatement = SyntaxFactory.ExpressionStatement(
                SyntaxFactory.InvocationExpression(SyntaxFactory.IdentifierName(newMethodName),
                    SyntaxFactory.ArgumentList(SyntaxFactory.SeparatedList(parameters.Select(p =>
                        SyntaxFactory.Argument(SyntaxFactory.IdentifierName(p.Identifier.Text)))))));
        }
        else if (allPathsReturnOrThrow)
        {
            returnType = SyntaxFactory.ParseTypeName("double"); // fallback or use semantic model to infer
            callStatement = SyntaxFactory.ReturnStatement(
                SyntaxFactory.InvocationExpression(
                    SyntaxFactory.IdentifierName(newMethodName),
                    SyntaxFactory.ArgumentList(SyntaxFactory.SeparatedList(parameters.Select(p =>
                        SyntaxFactory.Argument(SyntaxFactory.IdentifierName(p.Identifier.Text)))))));
        }
        else if (returnSymbol is ILocalSymbol localReturnSymbol)
        {
            returnType = SyntaxFactory.ParseTypeName(localReturnSymbol.Type.ToDisplayString());
            returnStatement = SyntaxFactory.ReturnStatement(SyntaxFactory.IdentifierName(localReturnSymbol.Name));

            if (selectedStatements.Count == 1 && selectedStatements.First() is ReturnStatementSyntax)
            {
                callStatement = SyntaxFactory.ReturnStatement(
                    SyntaxFactory.InvocationExpression(
                        SyntaxFactory.IdentifierName(newMethodName),
                        SyntaxFactory.ArgumentList(SyntaxFactory.SeparatedList(parameters.Select(p =>
                            SyntaxFactory.Argument(SyntaxFactory.IdentifierName(p.Identifier.Text)))))));
            }
            else
            {
                callStatement = SyntaxFactory.LocalDeclarationStatement(
                    SyntaxFactory.VariableDeclaration(returnType)
                        .WithVariables(SyntaxFactory.SingletonSeparatedList(
                            SyntaxFactory.VariableDeclarator(SyntaxFactory.Identifier(localReturnSymbol.Name))
                                .WithInitializer(SyntaxFactory.EqualsValueClause(
                                    SyntaxFactory.InvocationExpression(
                                        SyntaxFactory.IdentifierName(newMethodName),
                                        SyntaxFactory.ArgumentList(SyntaxFactory.SeparatedList(parameters.Select(p =>
                                            SyntaxFactory.Argument(SyntaxFactory.IdentifierName(p.Identifier.Text)))))))))));
            }
        }
        else
        {
            throw new InvalidOperationException("Unsupported return symbol type.");
        }

        // Create method body
        var newMethodBody = SyntaxFactory.Block(selectedStatements);
        if (returnStatement != null)
            newMethodBody = newMethodBody.AddStatements(returnStatement);

        var methodDeclaration = SyntaxFactory.MethodDeclaration(returnType, newMethodName)
            .AddModifiers(SyntaxFactory.Token(SyntaxKind.PrivateKeyword))
            .WithParameterList(SyntaxFactory.ParameterList(SyntaxFactory.SeparatedList(parameters)))
            .WithBody(newMethodBody);

        // Replace selected statements with call and insert method at end of class
        editor.ReplaceNode(selectedStatements.First(), callStatement);
        foreach (var stmt in selectedStatements.Skip(1))
            editor.RemoveNode(stmt);

        // Insert method after the containing method declaration
        var methodNode = block.Ancestors().OfType<MethodDeclarationSyntax>().FirstOrDefault();
        if (methodNode != null)
        {
            editor.InsertAfter(methodNode, methodDeclaration);
        }
        else
        {
            // fallback: insert after last selected statement
            editor.InsertAfter(selectedStatements.Last(), methodDeclaration);
        }

        return editor.GetChangedRoot().NormalizeWhitespace();
    }
}
