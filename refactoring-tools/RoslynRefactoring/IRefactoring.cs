using Microsoft.CodeAnalysis;

namespace RoslynRefactoring;

public interface IRefactoring
{
    string Description { get; }
    public Task<Document> PerformAsync(Document document);
}