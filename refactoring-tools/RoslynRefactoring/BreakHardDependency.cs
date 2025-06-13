using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Editing;
using Microsoft.CodeAnalysis.Text;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace RoslynRefactoring;

public class SelectionException : Exception
{
    public SelectionException(string message) : base(message) { }
}

public class BreakHardDependency : IRefactoring
{
    public string Description => "Convert hard field dependencies to constructor injection";
    
    private readonly CodeSelection _selection;

    public BreakHardDependency(CodeSelection selection)
    {
        _selection = selection ?? throw new ArgumentNullException(nameof(selection));
    }

    public static BreakHardDependency Create(string[] args)
    {
        if (args == null)
            throw new ArgumentNullException(nameof(args));
            
        if (args.Length == 0)
            throw new ArgumentException("Arguments array cannot be empty", nameof(args));
            
        var selection = CodeSelection.Parse(args[0]);
        return new BreakHardDependency(selection);
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
    
    private async Task<Document> ProcessDocumentAsync(Document document, SyntaxNode documentRoot, DocumentEditor documentEditor)
    {
        var (targetClass, singletonFields) = await FindTargetClassAndSingletonFields(document, documentRoot);
        
        if (targetClass == null || !singletonFields.Any())
            return document;
            
        var updatedClass = RefactorClass(targetClass, singletonFields);
        documentEditor.ReplaceNode(targetClass, updatedClass);
        
        UpdateObjectCreationExpressions(documentRoot, documentEditor, targetClass, singletonFields);
        
        return documentEditor.GetChangedDocument();
    }
    
    private async Task<(ClassDeclarationSyntax? TargetClass, List<(FieldDeclarationSyntax Field, string TypeName)> SingletonFields)> 
        FindTargetClassAndSingletonFields(Document document, SyntaxNode syntaxRoot)
    {
        var selectionResult = await TryFindFieldFromSelection(document, syntaxRoot);
        if (selectionResult.TargetClass != null && selectionResult.SingletonFields.Any())
            return selectionResult;
            
        return FindAllSingletonFields(syntaxRoot);
    }
    
    private async Task<(ClassDeclarationSyntax? TargetClass, List<(FieldDeclarationSyntax Field, string TypeName)> SingletonFields)>
        TryFindFieldFromSelection(Document document, SyntaxNode syntaxRoot)
    {
        var singletonFields = new List<(FieldDeclarationSyntax Field, string TypeName)>();
        
        try
        {
            if (!IsSelectionValid(_selection))
                throw new SelectionException("Invalid selection");
                
            var text = await document.GetTextAsync();
            var lines = text.Lines;
            
            if (!IsSelectionInRange(_selection, lines))
                throw new SelectionException("Selection out of range");
                
            var span = GetTextSpanFromSelection(lines);
            if (span == null)
                throw new SelectionException("Could not determine text span from selection");
                
            var selectedNode = syntaxRoot.FindNode(span.Value);
            var (fieldDeclaration, targetClass) = FindFieldAndClass(selectedNode);
            
            if (fieldDeclaration == null || targetClass == null)
                throw new SelectionException("Could not find field or class from selection");
                
            var singletonField = FindSingletonField(fieldDeclaration);
            if (singletonField != null)
                singletonFields.Add(singletonField.Value);
            
            return (targetClass, singletonFields);
        }
        catch (SelectionException)
        {
            return (null, singletonFields);
        }
    }
    
    private bool IsSelectionValid(CodeSelection selection)
    {
        return selection.Start.Line > 0 && selection.End.Line > 0;
    }
    
    private bool IsSelectionInRange(CodeSelection selection, TextLineCollection lines)
    {
        return selection.Start.Line <= lines.Count && selection.End.Line <= lines.Count;
    }
    
    private (FieldDeclarationSyntax? Field, ClassDeclarationSyntax? Class) FindFieldAndClass(SyntaxNode node)
    {
        var fieldDeclaration = node.AncestorsAndSelf().OfType<FieldDeclarationSyntax>().FirstOrDefault();
        if (fieldDeclaration == null)
            return (null, null);
            
        var targetClass = fieldDeclaration.Ancestors().OfType<ClassDeclarationSyntax>().FirstOrDefault();
        return (fieldDeclaration, targetClass);
    }
    
    private TextSpan? GetTextSpanFromSelection(TextLineCollection lines)
    {
        if (_selection.Start.Line < 1 || _selection.End.Line < 1 ||
            _selection.Start.Line > lines.Count || _selection.End.Line > lines.Count)
            return null;
            
        var startPos = lines[_selection.Start.Line - 1].Start +
            Math.Min(_selection.Start.Column - 1, lines[_selection.Start.Line - 1].End - lines[_selection.Start.Line - 1].Start);
        var endPos = lines[_selection.End.Line - 1].Start +
            Math.Min(_selection.End.Column - 1, lines[_selection.End.Line - 1].End - lines[_selection.End.Line - 1].Start);
        
        if (startPos <= endPos && startPos >= 0)
            return new TextSpan(startPos, endPos - startPos);
        
        return null;
    }
    
    private (FieldDeclarationSyntax Field, string TypeName)? FindSingletonField(FieldDeclarationSyntax fieldDeclaration)
    {
        var singletonVariable = fieldDeclaration.Declaration.Variables
            .FirstOrDefault(v =>
                v.Initializer?.Value is MemberAccessExpressionSyntax memberAccess &&
                memberAccess.Name.Identifier.Text == "Instance");
                
        if (singletonVariable == null)
            return null;
            
        var memberAccess = (MemberAccessExpressionSyntax)singletonVariable.Initializer!.Value;
        var typeName = memberAccess.Expression.ToString();
        
        return (fieldDeclaration, typeName);
    }
    
    private (ClassDeclarationSyntax? TargetClass, List<(FieldDeclarationSyntax Field, string TypeName)> SingletonFields)
        FindAllSingletonFields(SyntaxNode syntaxRoot)
    {
        var classDeclarations = syntaxRoot.DescendantNodes().OfType<ClassDeclarationSyntax>();
        
        foreach (var classDeclaration in classDeclarations)
        {
            var singletonFields = GetSingletonFieldsFromClass(classDeclaration);
            
            if (singletonFields.Any())
                return (classDeclaration, singletonFields);
        }
        
        return (null, new List<(FieldDeclarationSyntax Field, string TypeName)>());
    }
    
    private List<(FieldDeclarationSyntax Field, string TypeName)> GetSingletonFieldsFromClass(ClassDeclarationSyntax classDeclaration)
    {
        return classDeclaration.Members
            .OfType<FieldDeclarationSyntax>()
            .Select(field => FindSingletonField(field))
            .Where(field => field != null)
            .Select(field => field!.Value)
            .ToList();
    }
    
    private ClassDeclarationSyntax RefactorClass(
        ClassDeclarationSyntax classDeclaration,
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var updatedMembers = new List<MemberDeclarationSyntax>();
        
        var categorizedMembers = CategorizeMembersForRefactoring(classDeclaration, singletonFields);
        
        updatedMembers.AddRange(categorizedMembers.ModifiedFields);
        updatedMembers.AddRange(GetUpdatedConstructors(classDeclaration, categorizedMembers.Constructors, singletonFields));
        updatedMembers.AddRange(categorizedMembers.OtherMembers);
        
        return classDeclaration.WithMembers(SyntaxFactory.List(updatedMembers));
    }
    
    private List<MemberDeclarationSyntax> GetUpdatedConstructors(
        ClassDeclarationSyntax classDeclaration,
        List<ConstructorDeclarationSyntax> constructors,
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        if (constructors.Any())
        {
            return UpdateExistingConstructors(constructors, singletonFields)
                .Cast<MemberDeclarationSyntax>()
                .ToList();
        }
        
        return CreateConstructorsForSingletons(classDeclaration.Identifier.Text, singletonFields)
            .Cast<MemberDeclarationSyntax>()
            .ToList();
    }
    
    private class CategorizedMembers
    {
        public List<MemberDeclarationSyntax> ModifiedFields { get; } = new List<MemberDeclarationSyntax>();
        public List<ConstructorDeclarationSyntax> Constructors { get; } = new List<ConstructorDeclarationSyntax>();
        public List<MemberDeclarationSyntax> OtherMembers { get; } = new List<MemberDeclarationSyntax>();
    }
    
    private CategorizedMembers CategorizeMembersForRefactoring(
        ClassDeclarationSyntax classDeclaration,
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var result = new CategorizedMembers();
        
        foreach (var member in classDeclaration.Members)
        {
            if (member is FieldDeclarationSyntax fieldDeclaration)
            {
                var singletonField = singletonFields.FirstOrDefault(f => f.Field == fieldDeclaration);
                
                if (singletonField != default)
                {
                    var modifiedField = ConvertToReadonlyField(fieldDeclaration);
                    result.ModifiedFields.Add(modifiedField);
                }
                else
                {
                    result.ModifiedFields.Add(fieldDeclaration);
                }
            }
            else if (member is ConstructorDeclarationSyntax constructor)
            {
                result.Constructors.Add(constructor);
            }
            else
            {
                result.OtherMembers.Add(member);
            }
        }
        
        return result;
    }
    
    private FieldDeclarationSyntax ConvertToReadonlyField(FieldDeclarationSyntax fieldDeclaration)
    {
        var variable = fieldDeclaration.Declaration.Variables.First();
        var newVariable = variable.WithInitializer(null);
        
        var newDeclaration = fieldDeclaration.Declaration.WithVariables(
            SyntaxFactory.SingletonSeparatedList(newVariable));
            
        return fieldDeclaration
            .WithDeclaration(newDeclaration)
            .WithModifiers(SyntaxFactory.TokenList(
                SyntaxFactory.Token(SyntaxKind.PrivateKeyword),
                SyntaxFactory.Token(SyntaxKind.ReadOnlyKeyword)));
    }
    
    private void UpdateObjectCreationExpressions(
        SyntaxNode syntaxRoot, 
        DocumentEditor documentEditor, 
        ClassDeclarationSyntax targetClass, 
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var objectCreationExpressions = syntaxRoot.DescendantNodes().OfType<ObjectCreationExpressionSyntax>();
        var className = targetClass.Identifier.Text;
        
        foreach (var objectCreation in objectCreationExpressions)
        {
            var typeName = objectCreation.Type.ToString();
            
            if (typeName == className)
            {
                var updatedObjectCreation = UpdateObjectCreation(objectCreation, singletonFields);
                documentEditor.ReplaceNode(objectCreation, updatedObjectCreation);
            }
        }
    }
    
    private ObjectCreationExpressionSyntax UpdateObjectCreation(
        ObjectCreationExpressionSyntax objectCreation,
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var existingArguments = objectCreation.ArgumentList?.Arguments.ToList() ?? new List<ArgumentSyntax>();
        
        foreach (var singletonField in singletonFields)
        {
            var singletonArgument = SyntaxFactory.Argument(
                SyntaxFactory.MemberAccessExpression(
                    SyntaxKind.SimpleMemberAccessExpression,
                    SyntaxFactory.IdentifierName(singletonField.TypeName),
                    SyntaxFactory.IdentifierName("Instance")
                )
            );
            
            existingArguments.Add(singletonArgument);
        }
        
        var updatedArgumentList = SyntaxFactory.ArgumentList(SyntaxFactory.SeparatedList(existingArguments));
        
        return objectCreation.WithArgumentList(updatedArgumentList);
    }
    
    private List<ConstructorDeclarationSyntax> UpdateExistingConstructors(
        List<ConstructorDeclarationSyntax> constructors,
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var result = new List<ConstructorDeclarationSyntax>();
        
        foreach (var constructor in constructors)
        {
            var preservedConstructor = UpdateOriginalConstructor(constructor, singletonFields);
            result.Add(preservedConstructor);
            
            var newConstructor = CreateDependencyInjectionConstructor(constructor, singletonFields);
            if (newConstructor != null)
                result.Add(newConstructor);
        }
        
        return result;
    }
    
    private ConstructorDeclarationSyntax UpdateOriginalConstructor(
        ConstructorDeclarationSyntax constructor,
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var originalStatements = constructor.Body?.Statements.ToList() ?? new List<StatementSyntax>();
        var updatedStatements = new List<StatementSyntax>(originalStatements);
        
        foreach (var singletonField in singletonFields)
        {
            var fieldName = singletonField.Field.Declaration.Variables.First().Identifier.Text;
            
            if (!HasFieldAssignment(updatedStatements, fieldName))
            {
                var singletonAssignment = CreateSingletonAssignment(fieldName, singletonField.TypeName);
                updatedStatements.Add(singletonAssignment);
            }
        }
        
        return constructor.WithBody(SyntaxFactory.Block(updatedStatements));
    }
    
    private bool HasFieldAssignment(List<StatementSyntax> statements, string fieldName)
    {
        return statements.Any(s =>
            s is ExpressionStatementSyntax expr &&
            expr.Expression is AssignmentExpressionSyntax assignment &&
            assignment.Left.ToString() == fieldName);
    }
    
    private ConstructorDeclarationSyntax? CreateDependencyInjectionConstructor(
        ConstructorDeclarationSyntax baseConstructor,
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var updatedParameters = baseConstructor.ParameterList.Parameters.ToList();
        var updatedStatements = baseConstructor.Body?.Statements.ToList() ?? new List<StatementSyntax>();
        
        updatedStatements = updatedStatements
            .Where(s => !(s is ExpressionStatementSyntax expr &&
                          expr.Expression is AssignmentExpressionSyntax assignment &&
                          assignment.Right.ToString().Contains(".Instance")))
            .ToList();
        
        var newParameters = new List<ParameterSyntax>();
        var newAssignments = new List<StatementSyntax>();
        
        foreach (var singletonField in singletonFields)
        {
            var fieldName = singletonField.Field.Declaration.Variables.First().Identifier.Text;
            var paramName = FirstCharToLower(singletonField.TypeName);
            
            var parameterExists = updatedParameters.Any(p =>
                p.Type?.ToString() == singletonField.TypeName);
                
            if (!parameterExists)
            {
                var newParameter = SyntaxFactory.Parameter(
                    SyntaxFactory.Identifier(paramName))
                    .WithType(SyntaxFactory.IdentifierName(singletonField.TypeName));
                    
                newParameters.Add(newParameter);
                
                var assignment = CreateParameterAssignment(fieldName, paramName);
                newAssignments.Add(assignment);
            }
        }
        
        if (newParameters.Any())
        {
            var allParameters = updatedParameters.Concat(newParameters).ToList();
            var allStatements = updatedStatements.Concat(newAssignments).ToList();
            
            return baseConstructor
                .WithParameterList(SyntaxFactory.ParameterList(SyntaxFactory.SeparatedList(allParameters)))
                .WithBody(SyntaxFactory.Block(allStatements));
        }
        
        return null;
    }
    
    private List<ConstructorDeclarationSyntax> CreateConstructorsForSingletons(
        string className,
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var result = new List<ConstructorDeclarationSyntax>();
        
        var originalAssignments = singletonFields
            .Select(f => {
                var fieldName = f.Field.Declaration.Variables.First().Identifier.Text;
                return CreateSingletonAssignment(fieldName, f.TypeName);
            })
            .ToArray();
            
        var originalConstructorBody = SyntaxFactory.Block(originalAssignments);
        
        var originalConstructor = SyntaxFactory.ConstructorDeclaration(className)
            .WithModifiers(SyntaxFactory.TokenList(SyntaxFactory.Token(SyntaxKind.PublicKeyword)))
            .WithParameterList(SyntaxFactory.ParameterList())
            .WithBody(originalConstructorBody);
            
        result.Add(originalConstructor);
        
        var parameters = singletonFields
            .Select(f =>
                SyntaxFactory.Parameter(
                    SyntaxFactory.Identifier(FirstCharToLower(f.TypeName)))
                .WithType(SyntaxFactory.IdentifierName(f.TypeName)))
            .ToArray();
            
        var parameterList = SyntaxFactory.ParameterList(SyntaxFactory.SeparatedList(parameters));
        
        var assignments = singletonFields
            .Select(f => {
                var fieldName = f.Field.Declaration.Variables.First().Identifier.Text;
                return CreateParameterAssignment(fieldName, FirstCharToLower(f.TypeName));
            })
            .ToArray();
            
        var constructorBody = SyntaxFactory.Block(assignments);
        
        var newConstructor = SyntaxFactory.ConstructorDeclaration(className)
            .WithModifiers(SyntaxFactory.TokenList(SyntaxFactory.Token(SyntaxKind.PublicKeyword)))
            .WithParameterList(parameterList)
            .WithBody(constructorBody);
            
        result.Add(newConstructor);
        
        return result;
    }
    
    private StatementSyntax CreateSingletonAssignment(string fieldName, string typeName)
    {
        return SyntaxFactory.ExpressionStatement(
            SyntaxFactory.AssignmentExpression(
                SyntaxKind.SimpleAssignmentExpression,
                SyntaxFactory.IdentifierName(fieldName),
                SyntaxFactory.MemberAccessExpression(
                    SyntaxKind.SimpleMemberAccessExpression,
                    SyntaxFactory.IdentifierName(typeName),
                    SyntaxFactory.IdentifierName("Instance")
                )
            )
        );
    }
    
    private StatementSyntax CreateParameterAssignment(string fieldName, string paramName)
    {
        return SyntaxFactory.ExpressionStatement(
            SyntaxFactory.AssignmentExpression(
                SyntaxKind.SimpleAssignmentExpression,
                SyntaxFactory.IdentifierName(fieldName),
                SyntaxFactory.IdentifierName(paramName)
            )
        );
    }
    
    private string FirstCharToLower(string text)
    {
        if (string.IsNullOrEmpty(text))
            return text;
            
        return $"{char.ToLower(text[0])}{text[1..]}";
    }
}