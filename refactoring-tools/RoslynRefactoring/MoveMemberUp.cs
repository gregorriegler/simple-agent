using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace RoslynRefactoring;

/// <summary>
/// Moves a member from a derived class to its base class when the member only uses base class members
/// </summary>
public class MoveMemberUp : IRefactoring
{
    private readonly string derivedClassName;
    private readonly string memberName;

    public MoveMemberUp(string derivedClassName, string memberName)
    {
        this.derivedClassName = derivedClassName;
        this.memberName = memberName;
    }

    public static MoveMemberUp Create(string[] args)
    {
        if (args.Length != 2)
        {
            throw new ArgumentException("MoveMemberUp requires exactly 2 arguments: derivedClassName and memberName");
        }

        var derivedClassName = args[0];
        var memberName = args[1];

        return new MoveMemberUp(derivedClassName, memberName);
    }

    public async Task<Document> PerformAsync(Document document)
    {
        var root = await document.GetSyntaxRootAsync();
        if (root == null) return document;

        // Find the derived class
        var derivedClass = root.DescendantNodes()
            .OfType<ClassDeclarationSyntax>()
            .FirstOrDefault(c => c.Identifier.ValueText == derivedClassName);

        if (derivedClass == null)
        {
            Console.WriteLine($"Error: Class '{derivedClassName}' not found");
            return document;
        }

        // Find the base class
        var baseClass = FindBaseClass(root, derivedClass);
        if (baseClass == null)
        {
            Console.WriteLine($"Error: Base class for '{derivedClassName}' not found");
            return document;
        }

        // Find the member to move
        var memberToMove = derivedClass.Members
            .OfType<MethodDeclarationSyntax>()
            .FirstOrDefault(m => m.Identifier.ValueText == memberName);

        if (memberToMove == null)
        {
            Console.WriteLine($"Error: Method '{memberName}' not found in class '{derivedClassName}'");
            return document;
        }

        // For now, just move the method without dependency analysis (walking skeleton)
        var newRoot = MoveMemberToBaseClass(root, derivedClass, baseClass, memberToMove);
        return document.WithSyntaxRoot(newRoot);
    }

    private ClassDeclarationSyntax? FindBaseClass(SyntaxNode root, ClassDeclarationSyntax derivedClass)
    {
        if (derivedClass.BaseList?.Types.FirstOrDefault()?.Type is IdentifierNameSyntax baseTypeName)
        {
            var baseClassName = baseTypeName.Identifier.ValueText;
            return root.DescendantNodes()
                .OfType<ClassDeclarationSyntax>()
                .FirstOrDefault(c => c.Identifier.ValueText == baseClassName);
        }
        return null;
    }

    private SyntaxNode MoveMemberToBaseClass(SyntaxNode root, ClassDeclarationSyntax derivedClass,
        ClassDeclarationSyntax baseClass, MethodDeclarationSyntax memberToMove)
    {
        // Remove the member from the derived class
        var updatedDerivedClass = derivedClass.RemoveNode(memberToMove, SyntaxRemoveOptions.KeepNoTrivia);
        if (updatedDerivedClass == null) return root;

        // Add the member to the base class
        var updatedBaseClass = baseClass.AddMembers(memberToMove);

        // Replace both classes in the root
        var newRoot = root.ReplaceNode(derivedClass, updatedDerivedClass);
        newRoot = newRoot.ReplaceNode(newRoot.DescendantNodes().OfType<ClassDeclarationSyntax>()
            .First(c => c.Identifier.ValueText == baseClass.Identifier.ValueText), updatedBaseClass);

        return newRoot;
    }
}
