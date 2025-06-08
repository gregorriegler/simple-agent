using Microsoft.CodeAnalysis;
using System.Threading.Tasks;

namespace RoslynAnalysis;

public interface IWorkspaceLoader
{
    Task<Project?> LoadProjectAsync(string projectPath);
}
