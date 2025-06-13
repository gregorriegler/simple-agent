using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Editing;
using Microsoft.CodeAnalysis.Text;
using System;
using System.Collections.Generic;
using System.Linq;

namespace RoslynRefactoring;

public class BreakHardDependency : IRefactoring
{
    private readonly CodeSelection _selection;

    public BreakHardDependency(CodeSelection selection)
    {
        _selection = selection;
    }

    public static BreakHardDependency Create(string[] args)
    {
        var selection = CodeSelection.Parse(args[0]);
        return new BreakHardDependency(selection);
    }

    public async Task<Document> PerformAsync(Document document)
    {
        var syntaxRoot = await document.GetSyntaxRootAsync();
        var semanticModel = await document.GetSemanticModelAsync();
        
        if (syntaxRoot == null || semanticModel == null)
            return document;
            
        var documentEditor = await DocumentEditor.CreateAsync(document);
        
        // Find the target class and singleton fields to refactor
        var (targetClass, singletonFields) = await FindTargetClassAndSingletonFields(document, syntaxRoot);
        
        // If no singleton fields found, return the document unchanged
        if (targetClass == null || !singletonFields.Any())
            return document;
            
        // Refactor the target class
        var updatedClass = RefactorClass(targetClass, singletonFields);
        documentEditor.ReplaceNode(targetClass, updatedClass);
        
        // Update all object creation expressions that create instances of the modified class
        UpdateObjectCreationExpressions(syntaxRoot, documentEditor, targetClass, singletonFields);
        
        return documentEditor.GetChangedDocument();
    }
    
    private async Task<(ClassDeclarationSyntax? TargetClass, List<(FieldDeclarationSyntax Field, string TypeName)> SingletonFields)> 
        FindTargetClassAndSingletonFields(Document document, SyntaxNode syntaxRoot)
    {
        // Try to use the selection to find a specific field
        var selectionResult = await TryFindFieldFromSelection(document, syntaxRoot);
        if (selectionResult.TargetClass != null && selectionResult.SingletonFields.Any())
            return selectionResult;
            
        // Fall back to automated finding if selection didn't yield results
        return FindAllSingletonFields(syntaxRoot);
    }
    
    private async Task<(ClassDeclarationSyntax? TargetClass, List<(FieldDeclarationSyntax Field, string TypeName)> SingletonFields)> 
        TryFindFieldFromSelection(Document document, SyntaxNode syntaxRoot)
    {
        var singletonFields = new List<(FieldDeclarationSyntax Field, string TypeName)>();
        ClassDeclarationSyntax? targetClass = null;
        
        // If no selection provided, return empty result
        if (_selection.Start.Line <= 0 || _selection.End.Line <= 0)
            return (null, singletonFields);
            
        try
        {
            var text = await document.GetTextAsync();
            var lines = text.Lines;
            
            // Check if selection is within valid range
            if (_selection.Start.Line > lines.Count || _selection.End.Line > lines.Count)
                return (null, singletonFields);
                
            // Get the span from the selection
            var span = GetTextSpanFromSelection(lines);
            if (span == null)
                return (null, singletonFields);
                
            // Find the node at the selection
            var selectedNode = syntaxRoot.FindNode(span.Value);
            
            // Find the field declaration that contains the selection
            var fieldDeclaration = selectedNode.AncestorsAndSelf().OfType<FieldDeclarationSyntax>().FirstOrDefault();
            if (fieldDeclaration == null)
                return (null, singletonFields);
                
            // Find the class that contains the field
            targetClass = fieldDeclaration.Ancestors().OfType<ClassDeclarationSyntax>().FirstOrDefault();
            if (targetClass == null)
                return (null, singletonFields);
                
            // Check if the field is a singleton field
            var singletonField = FindSingletonField(fieldDeclaration);
            if (singletonField != null)
                singletonFields.Add(singletonField.Value);
        }
        catch
        {
            // If there's any error with the selection, return empty result
            return (null, new List<(FieldDeclarationSyntax Field, string TypeName)>());
        }
        
        return (targetClass, singletonFields);
    }
    
    private TextSpan? GetTextSpanFromSelection(TextLineCollection lines)
    {
        try
        {
            var startPos = lines[_selection.Start.Line - 1].Start + 
                Math.Min(_selection.Start.Column - 1, lines[_selection.Start.Line - 1].End - lines[_selection.Start.Line - 1].Start);
            var endPos = lines[_selection.End.Line - 1].Start + 
                Math.Min(_selection.End.Column - 1, lines[_selection.End.Line - 1].End - lines[_selection.End.Line - 1].Start);
            
            if (startPos <= endPos && startPos >= 0)
                return new TextSpan(startPos, endPos - startPos);
        }
        catch
        {
            // If there's any error calculating the span, return null
        }
        
        return null;
    }
    
    private (FieldDeclarationSyntax Field, string TypeName)? FindSingletonField(FieldDeclarationSyntax fieldDeclaration)
    {
        foreach (var variable in fieldDeclaration.Declaration.Variables)
        {
            if (variable.Initializer != null &&
                variable.Initializer.Value is MemberAccessExpressionSyntax memberAccess &&
                memberAccess.Name.Identifier.Text == "Instance")
            {
                var typeName = memberAccess.Expression.ToString();
                return (fieldDeclaration, typeName);
            }
        }
        
        return null;
    }
    
    private (ClassDeclarationSyntax? TargetClass, List<(FieldDeclarationSyntax Field, string TypeName)> SingletonFields) 
        FindAllSingletonFields(SyntaxNode syntaxRoot)
    {
        // Find all class declarations in the document
        var classDeclarations = syntaxRoot.DescendantNodes().OfType<ClassDeclarationSyntax>();
        
        foreach (var classDeclaration in classDeclarations)
        {
            // Find all fields in the class
            var fields = classDeclaration.Members.OfType<FieldDeclarationSyntax>();
            
            // Find singleton fields (fields initialized with ClassName.Instance)
            var singletonFields = new List<(FieldDeclarationSyntax Field, string TypeName)>();
            
            foreach (var field in fields)
            {
                var singletonField = FindSingletonField(field);
                if (singletonField != null)
                    singletonFields.Add(singletonField.Value);
            }
            
            // If singleton fields found, return this class and its singleton fields
            if (singletonFields.Any())
                return (classDeclaration, singletonFields);
        }
        
        // If no singleton fields found in any class, return null
        return (null, new List<(FieldDeclarationSyntax Field, string TypeName)>());
    }
    
    private ClassDeclarationSyntax RefactorClass(
        ClassDeclarationSyntax classDeclaration, 
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var updatedMembers = new List<MemberDeclarationSyntax>();
        
        // Categorize members
        var (modifiedFields, constructors, otherMembers) = CategorizeMembersForRefactoring(classDeclaration, singletonFields);
        
        // Add members in the correct order
        updatedMembers.AddRange(modifiedFields);
        
        if (constructors.Any())
        {
            var updatedConstructors = UpdateExistingConstructors(constructors, singletonFields);
            updatedMembers.AddRange(updatedConstructors);
        }
        else
        {
            var newConstructors = CreateConstructorsForSingletons(classDeclaration.Identifier.Text, singletonFields);
            updatedMembers.AddRange(newConstructors);
        }
        
        updatedMembers.AddRange(otherMembers);
        
        return classDeclaration.WithMembers(SyntaxFactory.List(updatedMembers));
    }
    
    private (List<MemberDeclarationSyntax> ModifiedFields, 
             List<ConstructorDeclarationSyntax> Constructors, 
             List<MemberDeclarationSyntax> OtherMembers) 
        CategorizeMembersForRefactoring(
            ClassDeclarationSyntax classDeclaration, 
            List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var modifiedFields = new List<MemberDeclarationSyntax>();
        var constructors = new List<ConstructorDeclarationSyntax>();
        var otherMembers = new List<MemberDeclarationSyntax>();
        
        foreach (var member in classDeclaration.Members)
        {
            if (member is FieldDeclarationSyntax fieldDeclaration)
            {
                var singletonField = singletonFields.FirstOrDefault(f => f.Field == fieldDeclaration);
                
                if (singletonField != default)
                {
                    var modifiedField = ConvertToReadonlyField(fieldDeclaration);
                    modifiedFields.Add(modifiedField);
                }
                else
                {
                    modifiedFields.Add(fieldDeclaration);
                }
            }
            else if (member is ConstructorDeclarationSyntax constructor)
            {
                constructors.Add(constructor);
            }
            else
            {
                otherMembers.Add(member);
            }
        }
        
        return (modifiedFields, constructors, otherMembers);
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
        
        // Keep original constructors
        foreach (var constructor in constructors)
        {
            // Create a copy of the original constructor but update the body to use the singleton
            var originalStatements = constructor.Body?.Statements.ToList() ?? new List<StatementSyntax>();
            var updatedOriginalStatements = new List<StatementSyntax>(originalStatements);
            
            // Add assignments for singleton fields
            foreach (var singletonField in singletonFields)
            {
                var fieldName = singletonField.Field.Declaration.Variables.First().Identifier.Text;
                
                // Check if there's already an assignment for this field
                var hasAssignment = updatedOriginalStatements.Any(s =>
                    s is ExpressionStatementSyntax expr &&
                    expr.Expression is AssignmentExpressionSyntax assignment &&
                    assignment.Left.ToString() == fieldName);
                    
                if (!hasAssignment)
                {
                    var singletonAssignment = CreateSingletonAssignment(fieldName, singletonField.TypeName);
                    updatedOriginalStatements.Add(singletonAssignment);
                }
            }
            
            var preservedConstructor = constructor
                .WithBody(SyntaxFactory.Block(updatedOriginalStatements));
                
            result.Add(preservedConstructor);
            
            // Create a new constructor with dependency injection parameters
            var newConstructor = CreateDependencyInjectionConstructor(constructor, singletonFields);
            if (newConstructor != null)
                result.Add(newConstructor);
        }
        
        return result;
    }
    
    private ConstructorDeclarationSyntax? CreateDependencyInjectionConstructor(
        ConstructorDeclarationSyntax baseConstructor,
        List<(FieldDeclarationSyntax Field, string TypeName)> singletonFields)
    {
        var updatedParameters = baseConstructor.ParameterList.Parameters.ToList();
        var updatedStatements = baseConstructor.Body?.Statements.ToList() ?? new List<StatementSyntax>();
        
        // Remove singleton assignments if they exist
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
        
        // Create original constructor with no parameters that uses singletons
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
        
        // Create new constructor with dependency injection parameters
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
    
    private string FirstCharToLower(string input)
    {
        if (string.IsNullOrEmpty(input))
            return input;
            
        return char.ToLower(input[0]) + input.Substring(1);
    }
}