namespace RoslynAnalysis;

/// <summary>
/// Represents a method entry point with metadata for characterization testing.
/// </summary>
public record EntryPoint(
    /// <summary>
    /// Gets the fully qualified name of the method (namespace.class.method).
    /// </summary>
    string FullyQualifiedName,
    
    /// <summary>
    /// Gets the file path where the method is defined.
    /// </summary>
    string FilePath,
    
    /// <summary>
    /// Gets the line number where the method starts.
    /// </summary>
    int LineNumber,
    
    /// <summary>
    /// Gets the method signature (parameters and return type).
    /// </summary>
    string MethodSignature,
    
    /// <summary>
    /// Gets the count of unique methods this entry point can reach.
    /// </summary>
    int ReachableMethodsCount);
