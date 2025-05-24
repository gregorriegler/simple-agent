namespace extract_method_tool;

public class RefactorPlan
{
    public string ProjectPath { get; set; } = "";
    public string FileName { get; set; } = "";
    public string NewMethodName { get; set; } = "";
    public CodeSelection Selection { get; set; } = new();
}

public class CodeSelection
{
    public int StartLine { get; set; }
    public int StartColumn { get; set; }
    public int EndLine { get; set; }
    public int EndColumn { get; set; }
}
