using Microsoft.CodeAnalysis;

namespace RoslynRefactoring;

public interface IRefactoring
{
    public Task<Document> PerformAsync(Document document);
}