namespace RoslynAnalysis;

/// <summary>
/// Represents a method entry point with metadata for characterization testing.
/// </summary>
public class EntryPoint
{
    /// <summary>
    /// Gets the fully qualified name of the method (namespace.class.method).
    /// </summary>
    public string FullyQualifiedName { get; }
    
    /// <summary>
    /// Gets the file path where the method is defined.
    /// </summary>
    public string FilePath { get; }
    
    /// <summary>
    /// Gets the line number where the method starts.
    /// </summary>
    public int LineNumber { get; }
    
    /// <summary>
    /// Gets the method signature (parameters and return type).
    /// </summary>
    public string MethodSignature { get; }
    
    /// <summary>
    /// Gets the count of unique methods this entry point can reach.
    /// </summary>
    public int ReachableMethodsCount { get; }
    
    public EntryPoint(
        string fullyQualifiedName,
        string filePath,
        int lineNumber,
        string methodSignature,
        int reachableMethodsCount)
    {
        FullyQualifiedName = fullyQualifiedName;
        FilePath = filePath;
        LineNumber = lineNumber;
        MethodSignature = methodSignature;
        ReachableMethodsCount = reachableMethodsCount;
    }
}
