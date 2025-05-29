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
    if (name == "extract-method")
    {
        return ExtractMethod.Create(refactoringArguments);
    }

    throw new InvalidOperationException("Unknown refactoring");
}