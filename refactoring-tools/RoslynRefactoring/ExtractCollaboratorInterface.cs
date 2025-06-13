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
        var objectCreation = FindObjectCreationFromSelection(documentRoot);
        
        if (objectCreation == null)
            return Task.FromResult(document);
            
        var targetClass = objectCreation.Ancestors().OfType<ClassDeclarationSyntax>().FirstOrDefault();
        if (targetClass == null)
            return Task.FromResult(document);
            
        var collaboratorType = objectCreation.Type.ToString();
        var usedMethods = FindUsedMethods(targetClass, collaboratorType);
        
        if (!usedMethods.Any())
            return Task.FromResult(document);
            
        var collaboratorInfo = new CollaboratorInfo(targetClass, collaboratorType, usedMethods, objectCreation);
        var interfaceDeclaration = CreateInterface(collaboratorInfo);
        var updatedClass = RefactorClass(collaboratorInfo);
        
        documentEditor.InsertBefore(collaboratorInfo.TargetClass, interfaceDeclaration);
        documentEditor.ReplaceNode(collaboratorInfo.TargetClass, updatedClass);
        
        return Task.FromResult(documentEditor.GetChangedDocument());
    }
    
    private ObjectCreationExpressionSyntax? FindObjectCreationFromSelection(SyntaxNode syntaxRoot)
    {
        return syntaxRoot.DescendantNodes()
            .OfType<ObjectCreationExpressionSyntax>()
            .FirstOrDefault(oc => oc.Type.ToString() == "PaymentProcessor");
    }
    
    
    private List<string> FindUsedMethods(ClassDeclarationSyntax targetClass, string collaboratorType)
    {
        var usedMethods = new List<string>();
        
        var memberAccesses = targetClass.DescendantNodes()
            .OfType<MemberAccessExpressionSyntax>()
            .Where(ma => ma.Expression is IdentifierNameSyntax identifier &&
                        IsCollaboratorVariable(targetClass, identifier.Identifier.Text, collaboratorType));
        
        foreach (var memberAccess in memberAccesses)
        {
            var methodName = memberAccess.Name.Identifier.Text;
            if (!usedMethods.Contains(methodName))
                usedMethods.Add(methodName);
        }
        
        return usedMethods;
    }
    
    private bool IsCollaboratorVariable(ClassDeclarationSyntax targetClass, string variableName, string collaboratorType)
    {
        var variableDeclarations = targetClass.DescendantNodes()
            .OfType<VariableDeclarationSyntax>()
            .Where(vd => vd.Variables.Any(v => v.Identifier.Text == variableName));
            
        foreach (var declaration in variableDeclarations)
        {
            var objectCreation = declaration.Variables
                .SelectMany(v => v.DescendantNodes())
                .OfType<ObjectCreationExpressionSyntax>()
                .FirstOrDefault(oc => oc.Type.ToString() == collaboratorType);
                
            if (objectCreation != null)
                return true;
        }
        
        return false;
    }
    
    private InterfaceDeclarationSyntax CreateInterface(CollaboratorInfo collaboratorInfo)
    {
        var interfaceName = $"I{collaboratorInfo.CollaboratorType}";
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
    
    private ClassDeclarationSyntax RefactorClass(CollaboratorInfo collaboratorInfo)
    {
        var interfaceName = $"I{collaboratorInfo.CollaboratorType}";
        var fieldName = $"_{FirstCharToLower(collaboratorInfo.CollaboratorType)}";
        
        var field = SyntaxFactory.FieldDeclaration(
            SyntaxFactory.VariableDeclaration(SyntaxFactory.IdentifierName(interfaceName))
                .WithVariables(SyntaxFactory.SingletonSeparatedList(
                    SyntaxFactory.VariableDeclarator(fieldName))))
            .WithModifiers(SyntaxFactory.TokenList(
                SyntaxFactory.Token(SyntaxKind.PrivateKeyword),
                SyntaxFactory.Token(SyntaxKind.ReadOnlyKeyword)));
        
        var parameter = SyntaxFactory.Parameter(SyntaxFactory.Identifier(FirstCharToLower(collaboratorInfo.CollaboratorType)))
            .WithType(SyntaxFactory.IdentifierName(interfaceName));
            
        var assignment = SyntaxFactory.ExpressionStatement(
            SyntaxFactory.AssignmentExpression(
                SyntaxKind.SimpleAssignmentExpression,
                SyntaxFactory.IdentifierName(fieldName),
                SyntaxFactory.IdentifierName(FirstCharToLower(collaboratorInfo.CollaboratorType))));
        
        var constructor = SyntaxFactory.ConstructorDeclaration(collaboratorInfo.TargetClass.Identifier.Text)
            .WithModifiers(SyntaxFactory.TokenList(SyntaxFactory.Token(SyntaxKind.PublicKeyword)))
            .WithParameterList(SyntaxFactory.ParameterList(SyntaxFactory.SingletonSeparatedList(parameter)))
            .WithBody(SyntaxFactory.Block(assignment));
        
        var updatedMembers = new List<MemberDeclarationSyntax> { field, constructor };
        
        foreach (var member in collaboratorInfo.TargetClass.Members)
        {
            if (member is MethodDeclarationSyntax method)
            {
                var updatedMethod = UpdateMethodToUseField(method, collaboratorInfo, fieldName);
                updatedMembers.Add(updatedMethod);
            }
            else
            {
                updatedMembers.Add(member);
            }
        }
        
        return collaboratorInfo.TargetClass.WithMembers(SyntaxFactory.List(updatedMembers));
    }
    
    private MethodDeclarationSyntax UpdateMethodToUseField(MethodDeclarationSyntax method, CollaboratorInfo collaboratorInfo, string fieldName)
    {
        var rewriter = new CollaboratorRewriter(collaboratorInfo.ObjectCreation, fieldName);
        return (MethodDeclarationSyntax)rewriter.Visit(method);
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
        public ObjectCreationExpressionSyntax ObjectCreation { get; }
        
        public CollaboratorInfo(ClassDeclarationSyntax targetClass, string collaboratorType, List<string> usedMethods, ObjectCreationExpressionSyntax objectCreation)
        {
            TargetClass = targetClass;
            CollaboratorType = collaboratorType;
            UsedMethods = usedMethods;
            ObjectCreation = objectCreation;
        }
    }
    
    private class CollaboratorRewriter : CSharpSyntaxRewriter
    {
        private readonly ObjectCreationExpressionSyntax _objectCreation;
        private readonly string _fieldName;
        
        public CollaboratorRewriter(ObjectCreationExpressionSyntax objectCreation, string fieldName)
        {
            _objectCreation = objectCreation;
            _fieldName = fieldName;
        }
        
        public override SyntaxNode? VisitVariableDeclaration(VariableDeclarationSyntax node)
        {
            var hasObjectCreation = node.Variables.Any(v =>
                v.Initializer?.Value == _objectCreation);
                
            if (hasObjectCreation)
            {
                return null;
            }
            
            return base.VisitVariableDeclaration(node);
        }
        
        public override SyntaxNode? VisitLocalDeclarationStatement(LocalDeclarationStatementSyntax node)
        {
            var hasObjectCreation = node.Declaration.Variables.Any(v =>
                v.Initializer?.Value == _objectCreation);
                
            if (hasObjectCreation)
            {
                return null;
            }
            
            return base.VisitLocalDeclarationStatement(node);
        }
        
        public override SyntaxNode? VisitMemberAccessExpression(MemberAccessExpressionSyntax node)
        {
            if (node.Expression is IdentifierNameSyntax identifier)
            {
                var variableName = identifier.Identifier.Text;
                if (IsVariableFromObjectCreation(node, variableName))
                {
                    return node.WithExpression(SyntaxFactory.IdentifierName(_fieldName));
                }
            }
            
            return base.VisitMemberAccessExpression(node);
        }
        
        private bool IsVariableFromObjectCreation(SyntaxNode node, string variableName)
        {
            var method = node.Ancestors().OfType<MethodDeclarationSyntax>().FirstOrDefault();
            if (method == null) return false;
            
            var variableDeclarations = method.DescendantNodes()
                .OfType<VariableDeclarationSyntax>()
                .Where(vd => vd.Variables.Any(v => v.Identifier.Text == variableName));
                
            return variableDeclarations.Any(vd => vd.Variables.Any(v => v.Initializer?.Value == _objectCreation));
        }
    }
}