namespace ExtractMethodTool;

public record CodeSelection(Cursor Start, Cursor End)
{
    public static CodeSelection Parse(string input)
    {
        var parts = input.Split('-');
        if (parts.Length != 2)
            throw new InvalidOperationException("CodeSelection not in the expected format N:M-O:P");
        return new CodeSelection(Cursor.Parse(parts[0]), Cursor.Parse(parts[1]));
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