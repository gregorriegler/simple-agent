using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Editing;
using System.Collections.Generic;
using System.Linq;

namespace RoslynRefactoring;

public class BreakHardDependency : IRefactoring
{
    public async Task<Document> PerformAsync(Document document)
    {
        var syntaxRoot = await document.GetSyntaxRootAsync();
        var semanticModel = await document.GetSemanticModelAsync();
        
        if (syntaxRoot == null || semanticModel == null)
            return document;
            
        var classDeclarations = syntaxRoot.DescendantNodes().OfType<ClassDeclarationSyntax>().ToList();
        var modifiedClasses = new Dictionary<string, (List<(FieldDeclarationSyntax Field, string TypeName)> Singletons, ClassDeclarationSyntax UpdatedClass)>();
        
        var documentEditor = await DocumentEditor.CreateAsync(document);
        
        foreach (var classDeclaration in classDeclarations)
        {
            var singletonFields = FindSingletonFields(classDeclaration);
            
            if (!singletonFields.Any())
                continue;
                
            var updatedMembers = new List<MemberDeclarationSyntax>();
            
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
                        var variable = fieldDeclaration.Declaration.Variables.First();
                        var newVariable = variable.WithInitializer(null);
                        
                        var newDeclaration = fieldDeclaration.Declaration.WithVariables(
                            SyntaxFactory.SingletonSeparatedList(newVariable));
                            
                        var newField = fieldDeclaration
                            .WithDeclaration(newDeclaration)
                            .WithModifiers(SyntaxFactory.TokenList(
                                SyntaxFactory.Token(SyntaxKind.PrivateKeyword),
                                SyntaxFactory.Token(SyntaxKind.ReadOnlyKeyword)));
                                
                        modifiedFields.Add(newField);
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
            
            var updatedClass = classDeclaration.WithMembers(SyntaxFactory.List(updatedMembers));
            documentEditor.ReplaceNode(classDeclaration, updatedClass);
            
            modifiedClasses.Add(classDeclaration.Identifier.Text, (singletonFields, updatedClass));
        }
        
        if (modifiedClasses.Any())
        {
            // Update all object creation expressions that create instances of the modified classes
            var objectCreationExpressions = syntaxRoot.DescendantNodes().OfType<ObjectCreationExpressionSyntax>();
            
            foreach (var objectCreation in objectCreationExpressions)
            {
                var typeName = objectCreation.Type.ToString();
                
                if (modifiedClasses.TryGetValue(typeName, out var classInfo))
                {
                    var updatedObjectCreation = UpdateObjectCreation(objectCreation, classInfo.Singletons);
                    documentEditor.ReplaceNode(objectCreation, updatedObjectCreation);
                }
            }
            
            return documentEditor.GetChangedDocument();
        }
        
        return document;
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
                    var singletonAssignment = SyntaxFactory.ExpressionStatement(
                        SyntaxFactory.AssignmentExpression(
                            SyntaxKind.SimpleAssignmentExpression,
                            SyntaxFactory.IdentifierName(fieldName),
                            SyntaxFactory.MemberAccessExpression(
                                SyntaxKind.SimpleMemberAccessExpression,
                                SyntaxFactory.IdentifierName(singletonField.TypeName),
                                SyntaxFactory.IdentifierName("Instance")
                            )
                        )
                    );
                    
                    updatedOriginalStatements.Add(singletonAssignment);
                }
            }
            
            var preservedConstructor = constructor
                .WithBody(SyntaxFactory.Block(updatedOriginalStatements));
                
            result.Add(preservedConstructor);
            
            // Create a new constructor with dependency injection parameters
            var updatedParameters = constructor.ParameterList.Parameters.ToList();
            var updatedStatements = constructor.Body?.Statements.ToList() ?? new List<StatementSyntax>();
            
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
                    
                    var assignment = SyntaxFactory.ExpressionStatement(
                        SyntaxFactory.AssignmentExpression(
                            SyntaxKind.SimpleAssignmentExpression,
                            SyntaxFactory.IdentifierName(fieldName),
                            SyntaxFactory.IdentifierName(paramName)
                        )
                    );
                    
                    newAssignments.Add(assignment);
                }
            }
            
            if (newParameters.Any())
            {
                var allParameters = updatedParameters.Concat(newParameters).ToList();
                var allStatements = updatedStatements.Concat(newAssignments).ToList();
                
                var newConstructor = constructor
                    .WithParameterList(SyntaxFactory.ParameterList(SyntaxFactory.SeparatedList(allParameters)))
                    .WithBody(SyntaxFactory.Block(allStatements));
                    
                result.Add(newConstructor);
            }
        }
        
        return result;
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
                return SyntaxFactory.ExpressionStatement(
                    SyntaxFactory.AssignmentExpression(
                        SyntaxKind.SimpleAssignmentExpression,
                        SyntaxFactory.IdentifierName(fieldName),
                        SyntaxFactory.MemberAccessExpression(
                            SyntaxKind.SimpleMemberAccessExpression,
                            SyntaxFactory.IdentifierName(f.TypeName),
                            SyntaxFactory.IdentifierName("Instance")
                        )
                    )
                );
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
                return SyntaxFactory.ExpressionStatement(
                    SyntaxFactory.AssignmentExpression(
                        SyntaxKind.SimpleAssignmentExpression,
                        SyntaxFactory.IdentifierName(fieldName),
                        SyntaxFactory.IdentifierName(FirstCharToLower(f.TypeName))
                    )
                );
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
    
    private List<(FieldDeclarationSyntax Field, string TypeName)> FindSingletonFields(ClassDeclarationSyntax classDeclaration)
    {
        var result = new List<(FieldDeclarationSyntax, string)>();
        
        foreach (var member in classDeclaration.Members)
        {
            if (member is FieldDeclarationSyntax fieldDeclaration)
            {
                foreach (var variable in fieldDeclaration.Declaration.Variables)
                {
                    if (variable.Initializer != null &&
                        variable.Initializer.Value is MemberAccessExpressionSyntax memberAccess &&
                        memberAccess.Name.Identifier.Text == "Instance")
                    {
                        var typeName = memberAccess.Expression.ToString();
                        result.Add((fieldDeclaration, typeName));
                    }
                }
            }
        }
        
        return result;
    }
    
    private string FirstCharToLower(string input)
    {
        if (string.IsNullOrEmpty(input))
            return input;
            
        return char.ToLower(input[0]) + input.Substring(1);
    }
}