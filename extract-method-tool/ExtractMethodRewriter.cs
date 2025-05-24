namespace extract_method_tool;

using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Editing;
using Microsoft.CodeAnalysis.Text;

public static class ExtractMethodRewriter
{
    public static async Task<SyntaxNode> RewriteAsync(Document document, TextSpan span, string newMethodName)
    {
        var root = await document.GetSyntaxRootAsync();
        var model = await document.GetSemanticModelAsync();

        // Print raw span content
        var spanText = root.GetText().ToString(span);
        Console.WriteLine("\n=== Raw Span Content ===\n" + spanText);
        
        // Find the common block ancestor
        var block = root.FindNode(span).AncestorsAndSelf().OfType<BlockSyntax>().FirstOrDefault();
        if (block == null)
            throw new InvalidOperationException("Selected statements are not inside a block.");

        // Filter direct child statements in the selected span
        var selectedStatements = block.Statements
            .Where(stmt => span.OverlapsWith(stmt.Span))
            .ToList();

        if (!selectedStatements.Any())
            throw new InvalidOperationException("No statements selected for extraction.");

        Console.WriteLine("\n=== Selected Block Statements ===");
        foreach (var stmt in selectedStatements)
            Console.WriteLine(stmt.ToFullString());
        
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

        if (returns.Count == 0)
        {
            returnType = SyntaxFactory.PredefinedType(SyntaxFactory.Token(SyntaxKind.VoidKeyword));
            callStatement = SyntaxFactory.ExpressionStatement(
                SyntaxFactory.InvocationExpression(SyntaxFactory.IdentifierName(newMethodName),
                    SyntaxFactory.ArgumentList(SyntaxFactory.SeparatedList(parameters.Select(p =>
                        SyntaxFactory.Argument(SyntaxFactory.IdentifierName(p.Identifier.Text)))))));
        }
        else if (returns.Count == 1)
        {
            var returnSymbol = returns.First();
            if (returnSymbol is ILocalSymbol localReturnSymbol)
            {
                returnType = SyntaxFactory.ParseTypeName(localReturnSymbol.Type.ToDisplayString());
                returnStatement = SyntaxFactory.ReturnStatement(SyntaxFactory.IdentifierName(localReturnSymbol.Name));
                callStatement = callStatement = SyntaxFactory.ExpressionStatement(
                    SyntaxFactory.AssignmentExpression(
                        SyntaxKind.SimpleAssignmentExpression,
                        SyntaxFactory.IdentifierName(localReturnSymbol.Name),
                        SyntaxFactory.InvocationExpression(SyntaxFactory.IdentifierName(newMethodName),
                            SyntaxFactory.ArgumentList(SyntaxFactory.SeparatedList(parameters.Select(p =>
                                SyntaxFactory.Argument(SyntaxFactory.IdentifierName(p.Identifier.Text))))))));
            }
            else
            {
                throw new InvalidOperationException("Unsupported return symbol type.");
            }
        }
        else
        {
            // Return tuple
            returnType = SyntaxFactory.TupleType(
                SyntaxFactory.SeparatedList(returns.Select(r =>
                    SyntaxFactory.TupleElement(SyntaxFactory.ParseTypeName((r as ILocalSymbol)?.Type.ToDisplayString() ?? "object"))
                        .WithIdentifier(SyntaxFactory.Identifier(r.Name)))));

            returnStatement = SyntaxFactory.ReturnStatement(
                SyntaxFactory.TupleExpression(
                    SyntaxFactory.SeparatedList(returns.Select(r =>
                        SyntaxFactory.Argument(SyntaxFactory.IdentifierName(r.Name))))));

            callStatement = SyntaxFactory.ExpressionStatement(
                SyntaxFactory.AssignmentExpression(SyntaxKind.SimpleAssignmentExpression,
                    SyntaxFactory.TupleExpression(
                        SyntaxFactory.SeparatedList(returns.Select(r =>
                            SyntaxFactory.Argument(SyntaxFactory.IdentifierName(r.Name))))),
                    SyntaxFactory.InvocationExpression(SyntaxFactory.IdentifierName(newMethodName),
                        SyntaxFactory.ArgumentList(SyntaxFactory.SeparatedList(parameters.Select(p =>
                            SyntaxFactory.Argument(SyntaxFactory.IdentifierName(p.Identifier.Text))))))));
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

        return editor.GetChangedRoot();
    }
}
