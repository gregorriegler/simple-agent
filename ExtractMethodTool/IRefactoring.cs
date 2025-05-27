using Microsoft.CodeAnalysis;

namespace ExtractMethodTool;

public interface IRefactoring
{
    public Task<Document> PerformAsync(Document document);
}