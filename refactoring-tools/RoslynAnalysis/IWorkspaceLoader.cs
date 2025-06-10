using Microsoft.CodeAnalysis;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace RoslynAnalysis;

public interface IWorkspaceLoader
{
    Task<IEnumerable<Project>> LoadProjectsAsync(string projectPath);
}
