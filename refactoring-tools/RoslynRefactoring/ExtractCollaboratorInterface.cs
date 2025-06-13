using System;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Editing;
using Microsoft.CodeAnalysis.Text;

namespace RoslynRefactoring;

public class ExtractCollaboratorInterface : IRefactoring
{
    private readonly CodeSelection _selection;

    public ExtractCollaboratorInterface(CodeSelection selection)
    {
        _selection = selection ?? throw new ArgumentNullException(nameof(selection));
    }

    public async Task<Document> PerformAsync(Document document)
    {
        if (document == null)
            throw new ArgumentNullException(nameof(document));
            
        var documentRoot = await document.GetSyntaxRootAsync();
        if (documentRoot == null)
            return document;
            
        var documentEditor = await DocumentEditor.CreateAsync(document);
        
        return await ProcessDocumentAsync(document, documentRoot, documentEditor);
    }
    
    private Task<Document> ProcessDocumentAsync(Document document, SyntaxNode documentRoot, DocumentEditor documentEditor)
    {
        var collaboratorInfo = ExtractCollaboratorInfo(documentRoot);
        
        if (collaboratorInfo == null)
            return Task.FromResult(document);
            
        ApplyRefactoring(documentEditor, collaboratorInfo);
        
        return Task.FromResult(documentEditor.GetChangedDocument());
    }
    
    private CollaboratorInfo? ExtractCollaboratorInfo(SyntaxNode documentRoot)
    {
        var collaboratorType = FindCollaboratorTypeFromSelection(documentRoot);
        
        if (collaboratorType == null)
            return null;
            
        var targetClass = FindTargetClass(collaboratorType);
        if (targetClass == null)
            return null;
            
        var typeName = collaboratorType.ToString();
        var usedMethods = FindUsedMethods(targetClass, typeName);
        
        if (!usedMethods.Any())
            return null;
            
        return new CollaboratorInfo(targetClass, typeName, usedMethods, null);
    }
    
    private ClassDeclarationSyntax? FindTargetClass(TypeSyntax collaboratorType)
    {
        return collaboratorType.Ancestors().OfType<ClassDeclarationSyntax>().FirstOrDefault();
    }
    
    private void ApplyRefactoring(DocumentEditor documentEditor, CollaboratorInfo collaboratorInfo)
    {
        var interfaceDeclaration = CreateInterface(collaboratorInfo);
        var updatedClass = RefactorClass(collaboratorInfo);
        
        documentEditor.InsertBefore(collaboratorInfo.TargetClass, interfaceDeclaration);
        documentEditor.ReplaceNode(collaboratorInfo.TargetClass, updatedClass);
    }
    
    private TypeSyntax? FindCollaboratorTypeFromSelection(SyntaxNode syntaxRoot)
    {
        // Find the first field declaration that could be a collaborator
        // This removes the hardcoded "PaymentProcessor" dependency
        return syntaxRoot.DescendantNodes()
            .OfType<FieldDeclarationSyntax>()
            .Where(f => IsLikelyCollaboratorType(f.Declaration.Type))
            .Select(f => f.Declaration.Type)
            .FirstOrDefault();
    }
    
    private bool IsLikelyCollaboratorType(TypeSyntax type)
    {
        var typeName = type.ToString();
        // A collaborator is likely a class type (not primitive, not generic collection)
        return !string.IsNullOrEmpty(typeName) &&
               char.IsUpper(typeName[0]) &&
               !typeName.Contains('<') &&
               !IsPrimitiveType(typeName);
    }
    
    private bool IsPrimitiveType(string typeName)
    {
        return typeName is "int" or "string" or "bool" or "double" or "float" or "decimal" or "DateTime";
    }
    
    
    private List<string> FindUsedMethods(ClassDeclarationSyntax targetClass, string collaboratorType)
    {
        var usedMethods = new List<string>();
        
        var memberAccesses = targetClass.DescendantNodes()
            .OfType<MemberAccessExpressionSyntax>()
            .Where(ma => ma.Expression is IdentifierNameSyntax identifier &&
                        IsCollaboratorField(targetClass, identifier.Identifier.Text, collaboratorType));
        
        foreach (var memberAccess in memberAccesses)
        {
            var methodName = memberAccess.Name.Identifier.Text;
            if (!usedMethods.Contains(methodName))
                usedMethods.Add(methodName);
        }
        
        return usedMethods;
    }
    
    private bool IsCollaboratorField(ClassDeclarationSyntax targetClass, string fieldName, string collaboratorType)
    {
        var fieldDeclarations = targetClass.DescendantNodes()
            .OfType<FieldDeclarationSyntax>()
            .Where(fd => fd.Declaration.Type.ToString() == collaboratorType &&
                        fd.Declaration.Variables.Any(v => v.Identifier.Text == fieldName));
            
        return fieldDeclarations.Any();
    }
    
    private InterfaceDeclarationSyntax CreateInterface(CollaboratorInfo collaboratorInfo)
    {
        var interfaceName = GetInterfaceName(collaboratorInfo.CollaboratorType);
        var methods = new List<MemberDeclarationSyntax>();
        
        foreach (var methodName in collaboratorInfo.UsedMethods)
        {
            var method = SyntaxFactory.MethodDeclaration(
                SyntaxFactory.PredefinedType(SyntaxFactory.Token(SyntaxKind.VoidKeyword)),
                methodName)
                .WithSemicolonToken(SyntaxFactory.Token(SyntaxKind.SemicolonToken));
                
            methods.Add(method);
        }
        
        return SyntaxFactory.InterfaceDeclaration(interfaceName)
            .WithModifiers(SyntaxFactory.TokenList(SyntaxFactory.Token(SyntaxKind.PublicKeyword)))
            .WithMembers(SyntaxFactory.List(methods));
    }
    
    private static string GetInterfaceName(string collaboratorType)
    {
        return $"I{collaboratorType}";
    }
    
    private ClassDeclarationSyntax RefactorClass(CollaboratorInfo collaboratorInfo)
    {
        var rewriter = new CollaboratorRewriter(collaboratorInfo.CollaboratorType, "");
        return (ClassDeclarationSyntax)rewriter.Visit(collaboratorInfo.TargetClass);
    }
    
    private string FirstCharToLower(string text)
    {
        if (string.IsNullOrEmpty(text))
            return text;
            
        return $"{char.ToLower(text[0])}{text[1..]}";
    }
    
    private class CollaboratorInfo
    {
        public ClassDeclarationSyntax TargetClass { get; }
        public string CollaboratorType { get; }
        public List<string> UsedMethods { get; }
        public ObjectCreationExpressionSyntax? ObjectCreation { get; }
        
        public CollaboratorInfo(ClassDeclarationSyntax targetClass, string collaboratorType, List<string> usedMethods, ObjectCreationExpressionSyntax? objectCreation)
        {
            TargetClass = targetClass;
            CollaboratorType = collaboratorType;
            UsedMethods = usedMethods;
            ObjectCreation = objectCreation;
        }
    }
    
    private class CollaboratorRewriter : CSharpSyntaxRewriter
    {
        private readonly string _collaboratorType;
        private readonly string _fieldName;
        
        public CollaboratorRewriter(string collaboratorType, string fieldName)
        {
            _collaboratorType = collaboratorType;
            _fieldName = fieldName;
        }
        
        public override SyntaxNode? VisitFieldDeclaration(FieldDeclarationSyntax node)
        {
            if (node.Declaration.Type.ToString() == _collaboratorType)
            {
                var interfaceName = GetInterfaceName(_collaboratorType);
                return node.WithDeclaration(
                    node.Declaration.WithType(SyntaxFactory.IdentifierName(interfaceName)));
            }
            
            return base.VisitFieldDeclaration(node);
        }
        
        public override SyntaxNode? VisitParameter(ParameterSyntax node)
        {
            if (node.Type?.ToString() == _collaboratorType)
            {
                var interfaceName = GetInterfaceName(_collaboratorType);
                return node.WithType(SyntaxFactory.IdentifierName(interfaceName));
            }
            
            return base.VisitParameter(node);
        }
    }
}