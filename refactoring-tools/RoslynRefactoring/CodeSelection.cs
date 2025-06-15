using Microsoft.CodeAnalysis.Text;

namespace RoslynRefactoring;

public record CodeSelection
{
    public Cursor Start { get; }
    public Cursor End { get; }

    private CodeSelection(Cursor start, Cursor end)
    {
        Start = start;
        End = end;
    }

    public static CodeSelection Create(Cursor start, Cursor end)
    {
        if (!IsValid(start, end))
            throw new InvalidOperationException("Invalid selection: line numbers must be greater than 0");
        return new CodeSelection(start, end);
    }

    public static CodeSelection Parse(string input)
    {
        var parts = input.Split('-');
        if (parts.Length != 2)
            throw new InvalidOperationException("CodeSelection not in the expected format N:M-O:P");
        var start = Cursor.Parse(parts[0]);
        var end = Cursor.Parse(parts[1]);
        return Create(start, end);
    }

    public bool IsInRange(TextLineCollection lines)
    {
        return Start.Line <= lines.Count && End.Line <= lines.Count;
    }

    private static bool IsValid(Cursor start, Cursor end)
    {
        return start.Line > 0 && end.Line > 0;
    }
}

public record Cursor(int Line, int Column)
{
    public static Cursor Parse(string input)
    {
        var parts = input.Split(':');
        if (parts.Length != 2)
            throw new InvalidOperationException("Cursor not in the expected format N:M");
        if (!int.TryParse(parts[0], out var line) || !int.TryParse(parts[1], out var column))
            throw new InvalidOperationException("Could not parse Cursor");
        return new Cursor(line, column);
    }
}