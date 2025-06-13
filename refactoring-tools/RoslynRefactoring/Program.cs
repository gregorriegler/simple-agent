using System.Reflection;
using RoslynRefactoring;

var refactoringName = args[0];

if (refactoringName == "--list-tools")
{
    var allRefactorings = GetAllRefactoringInfo();
    var toolsArray = allRefactorings.Values.Select(info => new
    {
        name = info.Name,
        description = info.Description,
        arguments = GetMergedArguments(info.Arguments)
    }).ToArray();

    var json = System.Text.Json.JsonSerializer.Serialize(toolsArray, new System.Text.Json.JsonSerializerOptions
    {
        WriteIndented = true
    });
    
    Console.WriteLine(json);
    return;
}

var refactoringArgs = args.Skip(3).ToArray();
var refactoring = CreateRefactoring(refactoringName, refactoringArgs);

var projectPath = args[1].Trim('"');
var fileName = args[2];
var project = new Project(projectPath, fileName);

await project.OpenAndApplyRefactoring(refactoring);
return;

Dictionary<string, RefactoringInfo> GetAllRefactoringInfo()
{
    var assembly = Assembly.GetExecutingAssembly();
    var refactoringTypes = assembly.GetTypes()
        .Where(t => typeof(IRefactoring).IsAssignableFrom(t) && !t.IsInterface && !t.IsAbstract)
        .ToList();

    var refactoringInfoMap = new Dictionary<string, RefactoringInfo>();
    
    foreach (var type in refactoringTypes)
    {
        var toolName = ConvertTypeNameToToolName(type.Name);
        var description = GetDescriptionFromType(type);
        var arguments = GetArgumentsFromType(type);
        
        refactoringInfoMap[toolName] = new RefactoringInfo(toolName, type, description, arguments);
    }
    
    return refactoringInfoMap;
}

string ConvertTypeNameToToolName(string typeName)
{
    var result = "";
    for (int i = 0; i < typeName.Length; i++)
    {
        if (i > 0 && char.IsUpper(typeName[i]))
        {
            result += "-";
        }
        result += char.ToLower(typeName[i]);
    }
    return result;
}

string GetDescriptionFromType(Type refactoringType)
{
    var descriptionProperty = refactoringType.GetProperty("StaticDescription", BindingFlags.Public | BindingFlags.Static);
    if (descriptionProperty == null)
    {
        return "No description available";
    }
    
    var description = descriptionProperty.GetValue(null);
    return description?.ToString() ?? "No description available";
}

string[] GetArgumentsFromType(Type refactoringType)
{
    var createMethod = refactoringType.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
    if (createMethod == null)
    {
        return Array.Empty<string>();
    }

    var parameters = createMethod.GetParameters();
    if (parameters.Length == 0 || parameters[0].ParameterType != typeof(string[]))
    {
        return Array.Empty<string>();
    }

    var constructors = refactoringType.GetConstructors();
    var primaryConstructor = constructors.FirstOrDefault();
    
    if (primaryConstructor == null)
    {
        return Array.Empty<string>();
    }

    var constructorParams = primaryConstructor.GetParameters();
    var argumentDescriptions = new List<string>();

    foreach (var param in constructorParams)
    {
        var paramName = param.Name ?? "unknown";
        var paramType = param.ParameterType.Name;
        argumentDescriptions.Add($"{paramName}: {paramType}");
    }

    return argumentDescriptions.ToArray();
}

string[] GetMergedArguments(string[] refactoringArguments)
{
    var programArgs = new[]
    {
        "project_path: string - Path to the project file",
        "file_name: string - Name of the file to refactor"
    };

    return programArgs.Concat(refactoringArguments).ToArray();
}

Dictionary<string, Type> GetAvailableRefactorings()
{
    return GetAllRefactoringInfo().ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Type);
}

IRefactoring CreateRefactoring(string name, string[] refactoringArguments)
{
    var refactoringMap = GetAvailableRefactorings();

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


record RefactoringInfo(string Name, Type Type, string Description, string[] Arguments);