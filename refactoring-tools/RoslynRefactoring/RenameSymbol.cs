using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Text;
using System.Linq;

namespace RoslynRefactoring;

/// <summary>
/// Renames a symbol at the specified cursor location to a new name
/// </summary>
public class RenameSymbol : IRefactoring
{
    private readonly Cursor cursor;
    private readonly string newName;

    public RenameSymbol(Cursor cursor, string newName)
    {
        this.cursor = cursor;
        this.newName = newName;
    }

    public static RenameSymbol Create(string[] args)
    {
        if (args.Length != 2)
        {
            throw new ArgumentException("RenameSymbol requires exactly 2 arguments: cursor and newName");
        }

        var cursor = Cursor.Parse(args[0]);
        var newName = args[1];

        return new RenameSymbol(cursor, newName);
    }

    public async Task<Document> PerformAsync(Document document)
    {
        var root = await document.GetSyntaxRootAsync();
        if (root == null) return document;

        var position = await GetCursorPosition(document);
        var token = root.FindToken(position);
        
        return await IdentifyAndRenameSymbolSolutionWide(document, root, token);
    }

    private async Task<int> GetCursorPosition(Document document)
    {
        var sourceText = await document.GetTextAsync();
        return sourceText.Lines[cursor.Line - 1].Start + cursor.Column - 1;
    }

    private async Task<Document> IdentifyAndRenameSymbolSolutionWide(Document document, SyntaxNode root, SyntaxToken token)
    {
        if (!IsValidRenameableToken(token))
        {
            return document;
        }

        var oldName = token.ValueText;

        var variableDeclarator = token.Parent as VariableDeclaratorSyntax;
        if (variableDeclarator != null)
        {
            return RenameVariable(document, root, variableDeclarator, oldName);
        }

        var methodDeclaration = token.Parent as MethodDeclarationSyntax;
        if (methodDeclaration != null)
        {
            return await RenameMethodSolutionWide(document, methodDeclaration, oldName);
        }

        PrintNoRenameableSymbolError();
        return document;
    }

    private static bool IsValidRenameableToken(SyntaxToken token)
    {
        if (!token.IsKind(SyntaxKind.IdentifierToken))
        {
            PrintNoRenameableSymbolError();
            return false;
        }
        return true;
    }

    private static void PrintNoRenameableSymbolError()
    {
        Console.WriteLine("Error: No renameable symbol found at cursor location. Supported symbol types: variables, methods");
    }


    private Document RenameVariable(Document document, SyntaxNode root, VariableDeclaratorSyntax variableDeclarator, string oldName)
    {
        var declarationScope = FindDeclarationScope(variableDeclarator);
        if (declarationScope == null)
            return document.WithSyntaxRoot(root);

        var referencesToRename = new List<SyntaxNode> { variableDeclarator };
        
        var identifiersInScope = declarationScope.DescendantNodes()
            .OfType<IdentifierNameSyntax>()
            .Where(id => id.Identifier.ValueText == oldName);

        foreach (var identifier in identifiersInScope)
        {
            if (IsReferenceToVariable(identifier, variableDeclarator, declarationScope))
            {
                referencesToRename.Add(identifier);
            }
        }

        var newRoot = root.ReplaceNodes(referencesToRename, (original, _) =>
        {
            return original switch
            {
                VariableDeclaratorSyntax declarator =>
                    declarator.WithIdentifier(SyntaxFactory.Identifier(newName)),
                IdentifierNameSyntax identifier =>
                    identifier.WithIdentifier(SyntaxFactory.Identifier(newName)),
                _ => original
            };
        });

        return document.WithSyntaxRoot(newRoot);
    }

    private Document RenameMethod(Document document, SyntaxNode root, MethodDeclarationSyntax methodDeclaration, string oldName)
    {
        var containingClass = methodDeclaration.FirstAncestorOrSelf<ClassDeclarationSyntax>();
        if (containingClass == null)
        {
            var newRoot = root.ReplaceNode(methodDeclaration,
                methodDeclaration.WithIdentifier(SyntaxFactory.Identifier(newName)));
            return document.WithSyntaxRoot(newRoot);
        }

        var referencesToRename = new List<SyntaxNode> { methodDeclaration };
        
        var methodCalls = containingClass.DescendantNodes()
            .OfType<InvocationExpressionSyntax>()
            .Where(invocation =>
            {
                if (invocation.Expression is IdentifierNameSyntax identifier)
                {
                    return identifier.Identifier.ValueText == oldName;
                }
                return false;
            });

        referencesToRename.AddRange(methodCalls.Select(call => call.Expression));

        var finalRoot = root.ReplaceNodes(referencesToRename, (original, _) =>
        {
            return original switch
            {
                MethodDeclarationSyntax method =>
                    method.WithIdentifier(SyntaxFactory.Identifier(newName)),
                IdentifierNameSyntax identifier =>
                    identifier.WithIdentifier(SyntaxFactory.Identifier(newName)),
                _ => original
            };
        });

        return document.WithSyntaxRoot(finalRoot);
    }

    private async Task<Document> RenameMethodSolutionWide(Document document, MethodDeclarationSyntax methodDeclaration, string oldName)
    {
        var solution = document.Project.Solution;
        var updatedSolution = solution;

        foreach (var project in solution.Projects)
        {
            foreach (var doc in project.Documents)
            {
                var docRoot = await doc.GetSyntaxRootAsync();
                if (docRoot == null) continue;

                var methodReferences = new List<SyntaxNode>();

                var methodDeclarations = FindMethodDeclarations(docRoot, oldName);
                methodReferences.AddRange(methodDeclarations);

                var methodCallExpressions = FindMethodCallExpressions(docRoot, oldName);
                methodReferences.AddRange(methodCallExpressions);

                if (methodReferences.Any())
                {
                    var updatedDocRoot = docRoot.ReplaceNodes(methodReferences, (original, _) =>
                    {
                        return original switch
                        {
                            MethodDeclarationSyntax method =>
                                method.WithIdentifier(SyntaxFactory.Identifier(newName)),
                            IdentifierNameSyntax identifier =>
                                identifier.WithIdentifier(SyntaxFactory.Identifier(newName)),
                            MemberAccessExpressionSyntax memberAccess when memberAccess.Name is IdentifierNameSyntax memberName =>
                                memberAccess.WithName(memberName.WithIdentifier(SyntaxFactory.Identifier(newName))),
                            _ => original
                        };
                    });

                    updatedSolution = updatedSolution.WithDocumentSyntaxRoot(doc.Id, updatedDocRoot);
                }
            }
        }

        var resultDocument = updatedSolution.GetDocument(document.Id);
        return resultDocument ?? document;
    }

    private static SyntaxNode? FindDeclarationScope(VariableDeclaratorSyntax variableDeclarator)
    {
        var current = variableDeclarator.Parent;
        while (current != null)
        {
            if (current is BlockSyntax or MethodDeclarationSyntax or ConstructorDeclarationSyntax)
            {
                return current;
            }
            current = current.Parent;
        }
        return null;
    }

    private static bool IsReferenceToVariable(IdentifierNameSyntax identifier, VariableDeclaratorSyntax targetVariable, SyntaxNode scope)
    {
        var identifierPosition = identifier.SpanStart;
        var targetPosition = targetVariable.SpanStart;
        
        if (identifierPosition <= targetPosition)
            return false;

        var blocksBetween = GetBlocksBetween(targetVariable, identifier, scope);
        
        foreach (var block in blocksBetween)
        {
            var shadowingDeclarations = block.DescendantNodes()
                .OfType<VariableDeclaratorSyntax>()
                .Where(v => v.Identifier.ValueText == targetVariable.Identifier.ValueText &&
                           v.SpanStart > targetPosition &&
                           v.SpanStart < identifierPosition);
                           
            if (shadowingDeclarations.Any())
            {
                return false;
            }
        }
        
        return true;
    }

    private static IEnumerable<SyntaxNode> GetBlocksBetween(SyntaxNode start, SyntaxNode end, SyntaxNode scope)
    {
        return scope.DescendantNodes()
            .OfType<BlockSyntax>()
            .Where(block => block.SpanStart >= start.SpanStart && block.Span.End <= end.Span.End);
    }

    private static IEnumerable<MethodDeclarationSyntax> FindMethodDeclarations(SyntaxNode root, string methodName)
    {
        return root.DescendantNodes()
            .OfType<MethodDeclarationSyntax>()
            .Where(method => method.Identifier.ValueText == methodName);
    }

    private static IEnumerable<SyntaxNode> FindMethodCallExpressions(SyntaxNode root, string methodName)
    {
        var methodCalls = root.DescendantNodes()
            .OfType<InvocationExpressionSyntax>()
            .Where(invocation =>
            {
                if (invocation.Expression is IdentifierNameSyntax identifier)
                {
                    return identifier.Identifier.ValueText == methodName;
                }
                if (invocation.Expression is MemberAccessExpressionSyntax memberAccess &&
                    memberAccess.Name is IdentifierNameSyntax memberName)
                {
                    return memberName.Identifier.ValueText == methodName;
                }
                return false;
            });
        
        return methodCalls.Select(call => call.Expression);
    }
}