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

        var sourceText = await document.GetTextAsync();
        var position = sourceText.Lines[cursor.Line - 1].Start + cursor.Column - 1;
        
        var token = root.FindToken(position);
        if (!token.IsKind(SyntaxKind.IdentifierToken))
            throw new InvalidOperationException("No renameable symbol found at cursor location");

        var oldName = token.ValueText;

        // Try to find a variable declarator first
        var variableDeclarator = token.Parent as VariableDeclaratorSyntax;
        if (variableDeclarator != null)
        {
            return RenameVariable(document, root, variableDeclarator, oldName);
        }

        // Try to find a method declaration
        var methodDeclaration = token.Parent as MethodDeclarationSyntax;
        if (methodDeclaration != null)
        {
            return RenameMethod(document, root, methodDeclaration, oldName);
        }

        throw new InvalidOperationException("No renameable symbol found at cursor location. Supported symbol types: variables, methods");
    }

    private Document RenameVariable(Document document, SyntaxNode root, VariableDeclaratorSyntax variableDeclarator, string oldName)
    {
        // Find the scope of this variable declaration
        var declarationScope = FindDeclarationScope(variableDeclarator);
        if (declarationScope == null)
            return document.WithSyntaxRoot(root);

        // Find all references to this variable within its scope
        var referencesToRename = new List<SyntaxNode> { variableDeclarator };
        
        // Find all identifier usages within the same scope
        var identifiersInScope = declarationScope.DescendantNodes()
            .OfType<IdentifierNameSyntax>()
            .Where(id => id.Identifier.ValueText == oldName);

        foreach (var identifier in identifiersInScope)
        {
            // Check if this identifier refers to our variable by checking if it's in the right scope
            if (IsReferenceToVariable(identifier, variableDeclarator, declarationScope))
            {
                referencesToRename.Add(identifier);
            }
        }

        // Replace all references
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
        // Find the class containing this method
        var containingClass = methodDeclaration.FirstAncestorOrSelf<ClassDeclarationSyntax>();
        if (containingClass == null)
        {
            // Just rename the method declaration if we can't find the containing class
            var newRoot = root.ReplaceNode(methodDeclaration,
                methodDeclaration.WithIdentifier(SyntaxFactory.Identifier(newName)));
            return document.WithSyntaxRoot(newRoot);
        }

        // Find all method calls within the same class
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

        // Replace all references
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

    private static SyntaxNode? FindDeclarationScope(VariableDeclaratorSyntax variableDeclarator)
    {
        // Walk up the syntax tree to find the containing scope
        var current = variableDeclarator.Parent;
        while (current != null)
        {
            // Look for block statements, method declarations, etc.
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
        // Simple scope-based check: if the identifier is in the same scope and there's no
        // shadowing variable declaration between the target and the identifier, it's a reference
        
        var identifierPosition = identifier.SpanStart;
        var targetPosition = targetVariable.SpanStart;
        
        // The identifier must come after the declaration
        if (identifierPosition <= targetPosition)
            return false;

        // Check if there's a shadowing declaration between target and identifier
        var blocksBetween = GetBlocksBetween(targetVariable, identifier, scope);
        
        foreach (var block in blocksBetween)
        {
            // Check if this block contains a variable declaration with the same name
            var shadowingDeclarations = block.DescendantNodes()
                .OfType<VariableDeclaratorSyntax>()
                .Where(v => v.Identifier.ValueText == targetVariable.Identifier.ValueText &&
                           v.SpanStart > targetPosition &&
                           v.SpanStart < identifierPosition);
                           
            if (shadowingDeclarations.Any())
            {
                // There's a shadowing declaration, so this identifier doesn't refer to our target
                return false;
            }
        }
        
        return true;
    }

    private static IEnumerable<SyntaxNode> GetBlocksBetween(SyntaxNode start, SyntaxNode end, SyntaxNode scope)
    {
        // Find all block syntax nodes that could contain shadowing declarations
        // between the start and end positions within the given scope
        return scope.DescendantNodes()
            .OfType<BlockSyntax>()
            .Where(block => block.SpanStart >= start.SpanStart && block.Span.End <= end.Span.End);
    }
}