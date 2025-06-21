namespace RoslynAnalysis;

public interface IAnalysis
{
    Task<object> AnalyzeAsync(Microsoft.CodeAnalysis.Project project, string fileName);
}