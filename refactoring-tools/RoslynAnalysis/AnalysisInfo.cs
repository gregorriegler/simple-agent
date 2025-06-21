using System.Reflection;

namespace RoslynAnalysis;

public static class AnalysisInfoGenerator
{
    public static object GetAllAnalysisInfo()
    {
        var analysisInfoMap = GetAvailableAnalyses();

        return analysisInfoMap.Values.Select(info =>
        {
            return new
            {
                name = info.Name,
                description = info.Description,
                arguments = new[]
                {
                    "project_path: string - Path to the project file",
                    "file_name: string - Name of the file to analyze"
                }.Concat(info.Arguments).ToArray()
            };
        }).ToArray();
    }

    public static IAnalysis CreateAnalysis(string name, string[] analysisArguments)
    {
        var analysisMap = GetAvailableAnalyses();

        if (!analysisMap.TryGetValue(name, out var analysisType))
        {
            var availableAnalyses = string.Join(", ", analysisMap.Keys);
            throw new InvalidOperationException(
                $"Unknown analysis '{name}'. Available analyses: {availableAnalyses}");
        }

        var createMethod = analysisType.Type.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
        if (createMethod == null)
        {
            throw new InvalidOperationException(
                $"Analysis '{analysisType.Name}' does not have a static Create method");
        }

        var result = createMethod.Invoke(null, [analysisArguments]);
        return (IAnalysis)result!;
    }

    private static Dictionary<string, AnalysisInfo> GetAvailableAnalyses()
    {
        var assembly = Assembly.GetExecutingAssembly();
        var analysisTypes = assembly.GetTypes()
            .Where(t => typeof(IAnalysis).IsAssignableFrom(t) && !t.IsInterface && !t.IsAbstract)
            .ToList();

        var analysisInfoMap = new Dictionary<string, AnalysisInfo>();

        foreach (var type in analysisTypes)
        {
            var toolName = ConvertTypeNameToToolName(type.Name);
            var description = GetDescriptionFromType(type);
            var arguments = GetArgumentsFromType(type);

            analysisInfoMap[toolName] = new AnalysisInfo(toolName, type, description, arguments);
        }

        return analysisInfoMap;
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

    private static string GetDescriptionFromType(Type analysisType)
    {
        try
        {
            var xmlDoc = System.Xml.Linq.XDocument.Load(GetXmlDocumentationPath());
            var typeName = analysisType.FullName;
            
            var summaryElement = xmlDoc.Descendants("member")
                .FirstOrDefault(m => m.Attribute("name")?.Value == $"T:{typeName}")
                ?.Element("summary");
                
            if (summaryElement != null)
            {
                return summaryElement.Value.Trim();
            }
        }
        catch
        {
        }
        
        return "No description available";
    }
    
    private static string GetXmlDocumentationPath()
    {
        var assemblyLocation = Assembly.GetExecutingAssembly().Location;
        var xmlPath = Path.ChangeExtension(assemblyLocation, ".xml");
        return xmlPath;
    }

    private static string[] GetArgumentsFromType(Type analysisType)
    {
        var createMethod = analysisType.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
        if (createMethod == null)
        {
            return [];
        }

        var parameters = createMethod.GetParameters();
        if (parameters.Length == 0 || parameters[0].ParameterType != typeof(string[]))
        {
            return [];
        }

        var constructors = analysisType.GetConstructors();
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

public record AnalysisInfo(string Name, Type Type, string Description, string[] Arguments);