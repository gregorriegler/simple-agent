using RoslynRefactoring;

var refactoringName = args[0];

if (refactoringName == "--list-tools")
{
    var allRefactorings = RefactoringInfoGenerator.GetAllRefactoringInfo();
    var json = System.Text.Json.JsonSerializer.Serialize(allRefactorings, new System.Text.Json.JsonSerializerOptions
    {
        WriteIndented = true
    });
    Console.WriteLine(json);
    return;
}

var refactoringArgs = args.Skip(3).ToArray();
var refactoring = RefactoringInfoGenerator.CreateRefactoring(refactoringName, refactoringArgs);

var projectPath = args[1].Trim('"');
var fileName = args[2];
var project = new CsProject(projectPath, fileName);

await project.OpenAndApplyRefactoring(refactoring);