namespace ExtractMethodTool;

public record Arguments(string ProjectPath, string FileName, string NewMethodName, CodeSelection Selection);

public record CodeSelection(int StartLine, int StartColumn, int EndLine, int EndColumn);
