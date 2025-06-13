using System.Reflection;
using RoslynRefactoring;

var refactoringName = args[0];

if (refactoringName == "--list-tools")
{
    var availableTools = GetAvailableRefactorings().Keys;
    foreach (var tool in availableTools)
    {
        Console.WriteLine(tool);
    }
    return;
}

if (refactoringName == "--describe" && args.Length >= 2)
{
    var toolName = args[1];
    var description = GetRefactoringDescription(toolName);
    Console.WriteLine(description);
    return;
}

if (refactoringName == "--arguments" && args.Length >= 2)
{
    var toolName = args[1];
    var arguments = GetRefactoringArguments(toolName);
    Console.WriteLine(arguments);
    return;
}

if (refactoringName == "--info" && args.Length >= 2)
{
    var toolName = args[1];
    var info = GetRefactoringInfo(toolName);
    Console.WriteLine(info);
    return;
}

var refactoringArgs = args.Skip(3).ToArray();
var refactoring = CreateRefactoring(refactoringName, refactoringArgs);

var projectPath = args[1].Trim('"');
var fileName = args[2];
var project = new Project(projectPath, fileName);

await project.OpenAndApplyRefactoring(refactoring);
return;

Dictionary<string, Type> GetAvailableRefactorings()
{
    var assembly = Assembly.GetExecutingAssembly();
    var refactoringTypes = assembly.GetTypes()
        .Where(t => typeof(IRefactoring).IsAssignableFrom(t) && !t.IsInterface && !t.IsAbstract)
        .ToList();

    var refactoringMap = new Dictionary<string, Type>();
    
    foreach (var type in refactoringTypes)
    {
        var toolName = ConvertTypeNameToToolName(type.Name);
        refactoringMap[toolName] = type;
    }
    
    return refactoringMap;
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

string GetRefactoringDescription(string name)
{
    var refactoringMap = GetAvailableRefactorings();

    if (!refactoringMap.TryGetValue(name, out var refactoringType))
    {
        var availableRefactorings = string.Join(", ", refactoringMap.Keys);
        throw new InvalidOperationException($"Unknown refactoring '{name}'. Available refactorings: {availableRefactorings}");
    }

    var descriptionProperty = refactoringType.GetProperty("StaticDescription", BindingFlags.Public | BindingFlags.Static);
    if (descriptionProperty == null)
    {
        throw new InvalidOperationException($"Refactoring '{refactoringType.Name}' does not have a StaticDescription property");
    }

    var description = descriptionProperty.GetValue(null);
    return description?.ToString() ?? "No description available";
}

string GetRefactoringArguments(string name)
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

    var parameters = createMethod.GetParameters();
    if (parameters.Length == 0 || parameters[0].ParameterType != typeof(string[]))
    {
        return "No arguments";
    }

    // Get argument information from the constructor or Create method
    var constructors = refactoringType.GetConstructors();
    var primaryConstructor = constructors.FirstOrDefault();
    
    if (primaryConstructor == null)
    {
        return "No constructor found";
    }

    var constructorParams = primaryConstructor.GetParameters();
    var argumentDescriptions = new List<string>();

    foreach (var param in constructorParams)
    {
        var paramName = param.Name ?? "unknown";
        var paramType = param.ParameterType.Name;
        argumentDescriptions.Add($"{paramName}: {paramType}");
    }

    return string.Join(", ", argumentDescriptions);
}

string GetRefactoringInfo(string name)
{
    var refactoringMap = GetAvailableRefactorings();

    if (!refactoringMap.TryGetValue(name, out var refactoringType))
    {
        var availableRefactorings = string.Join(", ", refactoringMap.Keys);
        throw new InvalidOperationException($"Unknown refactoring '{name}'. Available refactorings: {availableRefactorings}");
    }

    var description = GetRefactoringDescription(name);
    var arguments = GetRefactoringArguments(name);
    
    // Get program arguments (common to all tools)
    var programArgs = new[]
    {
        "project_path: string - Path to the project file",
        "file_name: string - Name of the file to refactor"
    };

    var result = new
    {
        name = name,
        description = description,
        program_arguments = programArgs,
        refactoring_arguments = arguments.Split(", ").Where(s => !string.IsNullOrEmpty(s)).ToArray()
    };

    return System.Text.Json.JsonSerializer.Serialize(result, new System.Text.Json.JsonSerializerOptions
    {
        WriteIndented = true
    });
}