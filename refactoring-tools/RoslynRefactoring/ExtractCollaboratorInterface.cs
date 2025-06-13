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
        var collaboratorType = FindFirstCollaboratorFieldType(documentRoot);
        
        if (collaboratorType == null)
            return null;
            
        var targetClass = FindTargetClass(collaboratorType);
        if (targetClass == null)
            return null;
            
        var typeName = collaboratorType.ToString();
        var usedMethods = FindUsedMethods(targetClass, typeName);
        var usedProperties = FindUsedProperties(targetClass, typeName);
        
        if (!usedMethods.Any() && !usedProperties.Any())
            return null;
            
        return new CollaboratorInfo(targetClass, typeName, usedMethods, usedProperties, null);
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
    
    private TypeSyntax? FindFirstCollaboratorFieldType(SyntaxNode syntaxRoot)
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
        var methodNames = new List<string>();
        
        var collaboratorMemberAccesses = targetClass.DescendantNodes()
            .OfType<MemberAccessExpressionSyntax>()
            .Where(memberAccess => memberAccess.Expression is IdentifierNameSyntax fieldIdentifier &&
                        IsCollaboratorField(targetClass, fieldIdentifier.Identifier.Text, collaboratorType));
        
        foreach (var memberAccess in collaboratorMemberAccesses)
        {
            if (IsMethodCall(memberAccess))
            {
                var methodName = memberAccess.Name.Identifier.Text;
                if (!methodNames.Contains(methodName))
                    methodNames.Add(methodName);
            }
        }
        
        return methodNames;
    }
    
    private bool IsMethodCall(MemberAccessExpressionSyntax memberAccess)
    {
        return memberAccess.Parent is InvocationExpressionSyntax;
    }
    
    private List<string> FindUsedProperties(ClassDeclarationSyntax targetClass, string collaboratorType)
    {
        var propertyNames = new List<string>();
        
        var collaboratorMemberAccesses = targetClass.DescendantNodes()
            .OfType<MemberAccessExpressionSyntax>()
            .Where(memberAccess => memberAccess.Expression is IdentifierNameSyntax fieldIdentifier &&
                        IsCollaboratorField(targetClass, fieldIdentifier.Identifier.Text, collaboratorType));
        
        foreach (var memberAccess in collaboratorMemberAccesses)
        {
            if (!IsMethodCall(memberAccess))
            {
                var propertyName = memberAccess.Name.Identifier.Text;
                if (!propertyNames.Contains(propertyName))
                    propertyNames.Add(propertyName);
            }
        }
        
        return propertyNames;
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
        var members = new List<MemberDeclarationSyntax>();
        
        foreach (var methodName in collaboratorInfo.UsedMethods)
        {
            var method = SyntaxFactory.MethodDeclaration(
                SyntaxFactory.PredefinedType(SyntaxFactory.Token(SyntaxKind.VoidKeyword)),
                methodName)
                .WithSemicolonToken(SyntaxFactory.Token(SyntaxKind.SemicolonToken));
                
            members.Add(method);
        }
        
        foreach (var propertyName in collaboratorInfo.UsedProperties)
        {
            var property = SyntaxFactory.PropertyDeclaration(
                SyntaxFactory.PredefinedType(SyntaxFactory.Token(SyntaxKind.ObjectKeyword)),
                propertyName)
                .WithAccessorList(SyntaxFactory.AccessorList(
                    SyntaxFactory.SingletonList(
                        SyntaxFactory.AccessorDeclaration(SyntaxKind.GetAccessorDeclaration)
                            .WithSemicolonToken(SyntaxFactory.Token(SyntaxKind.SemicolonToken)))));
                            
            members.Add(property);
        }
        
        return SyntaxFactory.InterfaceDeclaration(interfaceName)
            .WithModifiers(SyntaxFactory.TokenList(SyntaxFactory.Token(SyntaxKind.PublicKeyword)))
            .WithMembers(SyntaxFactory.List(members));
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
    
    private static string FirstCharToLower(string text)
    {
        return string.IsNullOrEmpty(text) ? text : char.ToLower(text[0]) + text[1..];
    }
    
    private class CollaboratorInfo
    {
        public ClassDeclarationSyntax TargetClass { get; }
        public string CollaboratorType { get; }
        public List<string> UsedMethods { get; }
        public List<string> UsedProperties { get; }
        public ObjectCreationExpressionSyntax? ObjectCreation { get; }
        
        public CollaboratorInfo(ClassDeclarationSyntax targetClass, string collaboratorType, List<string> usedMethods, List<string> usedProperties, ObjectCreationExpressionSyntax? objectCreation)
        {
            TargetClass = targetClass;
            CollaboratorType = collaboratorType;
            UsedMethods = usedMethods;
            UsedProperties = usedProperties;
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