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
        if (token.IsKind(SyntaxKind.IdentifierToken))
        {
            var variableDeclarator = token.Parent as VariableDeclaratorSyntax;
            if (variableDeclarator != null)
            {
                var oldName = token.ValueText;
                var newRoot = root.ReplaceNodes(
                    root.DescendantNodes().OfType<IdentifierNameSyntax>()
                        .Where(id => id.Identifier.ValueText == oldName)
                        .Cast<SyntaxNode>()
                        .Concat(new[] { variableDeclarator }),
                    (original, _) =>
                    {
                        if (original is VariableDeclaratorSyntax declarator)
                        {
                            return declarator.WithIdentifier(SyntaxFactory.Identifier(newName));
                        }
                        if (original is IdentifierNameSyntax identifier)
                        {
                            return identifier.WithIdentifier(SyntaxFactory.Identifier(newName));
                        }
                        return original;
                    });
                return document.WithSyntaxRoot(newRoot);
            }
        }

        return document;
    }
}