using System.Reflection;
using RoslynRefactoring;

var refactoringName = args[0];
var refactoringArgs = args.Skip(3).ToArray();
var refactoring = CreateRefactoring(refactoringName, refactoringArgs);

var projectPath = args[1].Trim('"');
var fileName = args[2];
var project = new Project(projectPath, fileName);

await project.OpenAndApplyRefactoring(refactoring);
return;

IRefactoring CreateRefactoring(string name, string[] refactoringArguments)
{
    var refactoringMap = new Dictionary<string, Type>
    {
        { "extract-method", typeof(ExtractMethod) },
        { "inline-method", typeof(InlineMethod) },
        { "extract-collaborator-interface", typeof(ExtractCollaboratorInterface) },
        { "break-hard-dependency", typeof(BreakHardDependency) }
    };

    if (!refactoringMap.TryGetValue(name, out var refactoringType))
    {
        var availableRefactorings = string.Join(", ", refactoringMap.Keys);
        throw new InvalidOperationException($"Unknown refactoring '{name}'. Available refactorings: {availableRefactorings}");
    }

    var createMethod = refactoringType.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
    if (createMethod == null)
    {
        throw new InvalidOperationException($"Refactoring '{refactoringType.Name}' does not have a static Create method");
    }

    var result = createMethod.Invoke(null, new object[] { refactoringArguments });
    return (IRefactoring)result!;
}