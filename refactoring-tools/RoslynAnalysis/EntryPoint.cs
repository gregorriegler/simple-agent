namespace RoslynAnalysis;

public record EntryPoint(
    string FullyQualifiedName,
    string FilePath,
    int LineNumber,
    string MethodSignature,
    int ReachableMethodsCount
);
