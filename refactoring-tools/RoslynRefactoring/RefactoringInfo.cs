using System.Reflection;
using System.IO;
using System.Xml.Linq;

namespace RoslynRefactoring;

public static class RefactoringInfoGenerator
{
    public static object GetAllRefactoringInfo()
    {
        var refactoringInfoMap = GetAvailableRefactorings();

        return refactoringInfoMap.Values.Select(info =>
        {
            return new
            {
                name = info.Name,
                description = info.Description,
                arguments = new[]
                {
                    "project_path: string - Path to the project file",
                    "file_name: string - Name of the file to refactor"
                }.Concat(info.Arguments).ToArray()
            };
        }).ToArray();
    }

    public static IRefactoring CreateRefactoring(string name, string[] refactoringArguments)
    {
        var refactoringMap = GetAvailableRefactorings();

        if (!refactoringMap.TryGetValue(name, out var refactoringType))
        {
            var availableRefactorings = string.Join(", ", refactoringMap.Keys);
            throw new InvalidOperationException(
                $"Unknown refactoring '{name}'. Available refactorings: {availableRefactorings}");
        }

        var createMethod = refactoringType.Type.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
        if (createMethod == null)
        {
            throw new InvalidOperationException(
                $"Refactoring '{refactoringType.Name}' does not have a static Create method");
        }

        var result = createMethod.Invoke(null, [refactoringArguments]);
        return (IRefactoring)result!;
    }

    private static Dictionary<string, RefactoringInfo> GetAvailableRefactorings()
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


    static string ConvertTypeNameToToolName(string typeName)
    {
        var result = "";
        for (var i = 0; i < typeName.Length; i++)
        {
            if (i > 0 && char.IsUpper(typeName[i]))
            {
                result += "-";
            }

            result += char.ToLower(typeName[i]);
        }

        return result;
    }

    private static string GetDescriptionFromType(Type refactoringType)
    {
        var xmlDoc = System.Xml.Linq.XDocument.Load(GetXmlDocumentationPath());
        var typeName = refactoringType.FullName;
        
        var summaryElement = xmlDoc.Descendants("member")
            .FirstOrDefault(m => m.Attribute("name")?.Value == $"T:{typeName}")
            ?.Element("summary");
            
        if (summaryElement != null)
        {
            return summaryElement.Value.Trim();
        }
        
        return "No description available";
    }
    
    private static string GetXmlDocumentationPath()
    {
        var assemblyLocation = Assembly.GetExecutingAssembly().Location;
        var xmlPath = Path.ChangeExtension(assemblyLocation, ".xml");
        return xmlPath;
    }

    private static string[] GetArgumentsFromType(Type refactoringType)
    {
        var createMethod = refactoringType.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
        if (createMethod == null)
        {
            return [];
        }

        var parameters = createMethod.GetParameters();
        if (parameters.Length == 0 || parameters[0].ParameterType != typeof(string[]))
        {
            return [];
        }

        var constructors = refactoringType.GetConstructors();
        var primaryConstructor = constructors.FirstOrDefault();

        if (primaryConstructor == null)
        {
            return [];
        }

        return (
            from param in primaryConstructor.GetParameters()
            let paramName = param.Name ?? "unknown"
            let paramType = param.ParameterType.Name
            select $"{paramName}: {paramType}"
        ).ToArray();
    }
}

public record RefactoringInfo(string Name, Type Type, string Description, string[] Arguments);